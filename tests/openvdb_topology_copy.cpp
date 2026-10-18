#include <openvdb/openvdb.h>
#include <cassert>
#include <iostream>
int main() {
  openvdb::initialize();
  openvdb::FloatTree source(0.0f);
  source.setValue(openvdb::Coord(1,2,3), 2.0f);
  source.fill(openvdb::CoordBBox(openvdb::Coord(64),openvdb::Coord(95)),3.0f,true);
  auto* leaf = source.probeLeaf(openvdb::Coord(1,2,3));
  leaf->setVersion(17);
  assert(leaf->incVersion() == 17);
  auto* node = source.root().probeChild(openvdb::Coord(1,2,3));
  node->setVersion(23);
  node->setValueOnly(openvdb::Coord(1,2,3), 4.0f);
  assert(node->getVersion() == 24);
  openvdb::FloatTree deep(source);
  assert(deep.probeLeaf(openvdb::Coord(1,2,3))->getVersion() == 18);
  assert(deep.root().probeChild(openvdb::Coord(1,2,3))->hash() == node->hash());
  for(float background : {0.0f,1.0f,-2.5f}) {
    openvdb::FloatTree copy(source, background, openvdb::TopologyCopy());
    assert(copy.getValue(openvdb::Coord(1,2,3)) == background);
    assert(copy.getValue(openvdb::Coord(70)) == background);
    assert(copy.getValue(openvdb::Coord(1000)) == background);
    assert(copy.activeVoxelCount() == source.activeVoxelCount());
    assert(copy.isValueOn(openvdb::Coord(1,2,3)));
    assert(copy.isValueOn(openvdb::Coord(70)));
    assert(!copy.isValueOn(openvdb::Coord(1000)));
  }
  openvdb::DoubleTree doubleCopy(source,1.0,openvdb::TopologyCopy());
  assert(doubleCopy.getValue(openvdb::Coord(1,2,3)) == 1.0);
  assert(doubleCopy.activeVoxelCount() == source.activeVoxelCount());
  std::cout << "VDB fork regression PASS: node versions/hash/deep copy, zero/nonzero/negative topology backgrounds, active tiles/voxels, cross-type copy\n";
}
