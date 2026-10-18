import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "bin_pub" / "obt.stage.clone.py"


class StageCloneTests(unittest.TestCase):
    def make_stage(self, root):
        stage = root / "source-stage"
        (stage / "lib").mkdir(parents=True)
        (stage / "bin").mkdir()
        (stage / "pyvenv").mkdir()
        stage = stage.resolve()
        (stage / "obt-launch-env").write_text(f"#!/bin/sh\n# {stage}\n")
        (stage / "pyvenv" / "pyvenv.cfg").write_text(f"prefix={stage}\n")
        (stage / "bin" / "absolute-lib").symlink_to(stage / "lib")
        return stage

    def test_relocates_text_symlink_and_manifest(self):
        with tempfile.TemporaryDirectory(prefix="obt-stage-clone-test-") as tmp:
            root = Path(tmp)
            source = self.make_stage(root)
            dest = root / "target-stage"
            subprocess.run([
                sys.executable, SCRIPT, "--source", source, "--dest", dest,
                "--skip-macho-fixup", "--full-copy"], check=True)
            dest = dest.resolve()
            self.assertNotIn(str(source), (dest / "pyvenv" / "pyvenv.cfg").read_text())
            self.assertIn(str(dest), (dest / "pyvenv" / "pyvenv.cfg").read_text())
            self.assertTrue(str((dest / "bin" / "absolute-lib").readlink()).startswith(str(dest)))
            manifest = json.loads((dest / "obt-stage-clone.json").read_text())
            self.assertTrue(manifest["verification"]["passed"])

    def test_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory(prefix="obt-stage-clone-test-") as tmp:
            root = Path(tmp)
            source = self.make_stage(root)
            dest = root / "target-stage"
            dest.mkdir()
            proc = subprocess.run([
                sys.executable, SCRIPT, "--source", source, "--dest", dest,
                "--skip-macho-fixup", "--full-copy"], text=True, capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("destination already exists", proc.stderr)

    def test_unrelocatable_large_binary_cannot_pass_verification(self):
        with tempfile.TemporaryDirectory(prefix="obt-stage-clone-test-") as tmp:
            root = Path(tmp)
            source = self.make_stage(root)
            payload = source / 'lib' / 'runtime-data.bin'
            with payload.open('wb') as out:
                out.write(b'\0runtime-data\0')
                out.seek(17 * 1024 * 1024)
                out.write(str(source / 'share' / 'settings').encode())
            dest = root / 'target-stage'
            proc = subprocess.run([sys.executable, SCRIPT, '--source', source, '--dest', dest,
                                   '--skip-macho-fixup', '--full-copy'], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('binary_embedded', proc.stderr)
            self.assertIn('runtime-data.bin', proc.stderr)
            self.assertFalse(dest.exists())
            self.assertTrue(payload.exists())

    def test_relative_directory_link_is_independent_of_source(self):
        with tempfile.TemporaryDirectory(prefix='obt-stage-link-') as tmp:
            root = Path(tmp).resolve()
            source = self.make_stage(root)
            (source/'lib'/'settings').write_text('settings')
            (source/'bin'/'relative-lib').symlink_to('../../source-stage/lib')
            dest = root/'target-stage'
            subprocess.run([sys.executable, SCRIPT, '--source', source, '--dest', dest,
                            '--skip-macho-fixup', '--full-copy'], check=True, capture_output=True)
            source.rename(root/'source-disabled')
            self.assertEqual((dest/'bin'/'relative-lib'/'settings').read_text(), 'settings')

    @unittest.skipUnless(sys.platform == 'darwin' or sys.platform.startswith('linux'), 'native binary test')
    def test_compiled_in_resource_path_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='obt-stage-runtime-') as tmp:
            root = Path(tmp).resolve()
            source = self.make_stage(root)
            code = root/'resource.c'
            code.write_text('#include <stdio.h>\nint main(void) { return fopen(' +
                            json.dumps(str(source/'lib'/'settings')) + ', "r") ? 0 : 7; }\n')
            subprocess.run(['cc', str(code), '-o', str(source/'bin'/'resource')], check=True)
            dest = root/'target-stage'
            result = subprocess.run([sys.executable, SCRIPT, '--source', source, '--dest', dest,
                                     '--skip-macho-fixup', '--full-copy'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('binary_embedded', result.stderr)
            self.assertIn('bin/resource', result.stderr)
            self.assertFalse(dest.exists())


@unittest.skipUnless(sys.platform.startswith('linux'), 'requires native Linux ELF tools')
class ElfCloneTests(unittest.TestCase):
    make_stage = StageCloneTests.make_stage
    def test_elf_loader_references_relocated_and_source_can_be_removed(self):
        for tool in ('cc', 'patchelf', 'readelf'):
            self.assertIsNotNone(shutil.which(tool), 'Linux clone tests require ' + tool)
        for legacy_rpath in (False, True):
            with self.subTest(legacy_rpath=legacy_rpath), tempfile.TemporaryDirectory(prefix='obt-elf-clone-') as tmp:
                root = Path(tmp).resolve()
                source = self.make_stage(root)
                dest = root / 'longer-destination-stage'
                lib = source / 'lib' / 'libfixture.so'
                # Absolute SONAME also creates an absolute NEEDED entry in the executable.
                (root/'lib.c').write_text('int answer(void) { return 42; }\n')
                (root/'main.c').write_text('extern int answer(void); int main(void) { return answer() == 42 ? 0 : 1; }\n')
                subprocess.run(['cc', '-shared', '-fPIC', str(root/'lib.c'), '-o', str(lib),
                                '-Wl,-soname,' + str(lib)], check=True)
                app = source/'bin'/'fixture'
                flags = ['-Wl,--disable-new-dtags'] if legacy_rpath else []
                subprocess.run(['cc', str(root/'main.c'), str(lib), '-o', str(app),
                                '-Wl,-rpath,' + str(source/'lib'), *flags], check=True)
                loader = subprocess.check_output(['patchelf', '--print-interpreter', str(app)], text=True).strip()
                relocated_loader = source/'lib'/'ld-fixture.so'
                shutil.copy2(loader, relocated_loader)
                subprocess.run(['patchelf', '--set-interpreter', str(relocated_loader), str(app)], check=True)
                result = subprocess.run([sys.executable, SCRIPT, '--source', source, '--dest', dest,
                                         '--full-copy'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                manifest = json.loads((dest/'obt-stage-clone.json').read_text())
                self.assertEqual(len(manifest['elf_files_rewritten']), 2)
                self.assertFalse(any(manifest['verification']['source_prefix_findings'].values()))
                source.rename(root/'source-disabled')
                environment = dict(os.environ)
                environment.pop('LD_LIBRARY_PATH', None)
                environment.pop('LD_PRELOAD', None)
                subprocess.run([str(dest/'bin'/'fixture')], env=environment, check=True)
                tags = subprocess.check_output(['readelf', '-d', str(dest/'bin'/'fixture')], text=True)
                self.assertIn('(RPATH)' if legacy_rpath else '(RUNPATH)', tags)


if __name__ == "__main__":
    unittest.main()
