from obt import pathtools

def try_update(content_path=None,manifest_path=None,update_method=None,force=False):
  md5_of_data = pathtools.md5_of_file(content_path)
  touch_manifest = False
  ###########################
  if manifest_path.exists():
    fil = open(str(manifest_path),"rb")
    manifest_md5 = fil.readline().decode("utf-8")
    fil.close()
    if md5_of_data != manifest_md5:
      touch_manifest = True
  else:
    touch_manifest = True
  ###########################
  if touch_manifest or force:
    update_method()
    # write md5 to manifest
    fil = open(str(manifest_path),"w")
    fil.write(md5_of_data)
    fil.close()
  ###########################


def try_update_on_content_list(content_paths=None,manifest_path=None,update_method=None,force=False):
  md5_of_data = pathtools.md5_of_files(content_paths)
  touch_manifest = False
  ###########################
  if manifest_path.exists():
    fil = open(str(manifest_path),"rb")
    manifest_md5 = fil.readline().decode("utf-8")
    fil.close()
    if md5_of_data != manifest_md5:
      touch_manifest = True
  else:
    touch_manifest = True
  ###########################
  if touch_manifest or force:
    update_method()
    # write md5 to manifest
    fil = open(str(manifest_path),"w")
    fil.write(md5_of_data)
    fil.close()
  ###########################

