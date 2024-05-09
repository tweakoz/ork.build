#import <Metal/Metal.h>
#import <QuartzCore/QuartzCore.h>
#import <UIKit/UIKit.h>
#include <assert.h>
#include <boost/filesystem.hpp>
#include <parsertl/parse.hpp>
#include <string>
#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>
#include "dll.h"
//#include <SQLiteCpp/SQLiteCpp.h>

///////////////////////////////////////////////////////////////////////////////

#define IS_IPHONE (UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone)

using mtl_fn_t = id<MTLFunction>;
using mtl_lib_t = id<MTLLibrary>;
using mtl_dev_t = id<MTLDevice>;
using mtl_drw_t = id<CAMetalDrawable>;
using mtl_cq_t = id<MTLCommandQueue>;
using mtl_pipe_t = id<MTLRenderPipelineState>;
using fquat = glm::quat;
using fvec3 = glm::vec3;

NSString* nsstrfromstr(const std::string& str) {
  return [NSString stringWithUTF8String:str.c_str()];
}
///////////////////////////////////////////////////////////////////////////////
// Metal shader functions
///////////////////////////////////////////////////////////////////////////////

std::string vertexShaderSource = R"xxx(                        
  #include <metal_stdlib>                               
  using namespace metal;                                
                                                        
  struct VertexIn {                                     
    float3 position [[attribute(0)]];                 
  };                                                    
                                                        
  vertex float4 vertexShader(VertexIn in [[stage_in]]) {
    return float4(in.position.xy, 0.0, 1.0);             
  }                                                     
)xxx";

///////////////////////////////////////////////////////////////////////////////

std::string fragmentShaderSource = R"xxx(                       
  #include <metal_stdlib>                               
  using namespace metal;                                
                                                        
  fragment float4 fragmentShader() {                    
    return float4(1.0, 0.0, 0.0, 1.0);                
  }                                                     
)xxx";

///////////////////////////////////////////////////////////////////////////////
// C++ code for rendering the triangle
///////////////////////////////////////////////////////////////////////////////

namespace {

void renderTriangle(mtl_dev_t device,      //
                    mtl_cq_t commandQueue, //
                    mtl_drw_t drawable,    //
                    mtl_pipe_t pipeline) { //

  static float phi = 0.0f;
  phi += 0.03f;

  float R = 0.5f * (sinf(phi * 0.5f) + 1.0f);
  float G = 0.5f * (sinf(phi * 0.7f) + 1.0f);
  float B = 0.5f * (sinf(phi * 0.9f) + 1.0f);

  fquat q = glm::angleAxis(phi, fvec3(0.0f, 0.0f, 1.0f));

  float r = 0.707;
  static fvec3 V[3];
  V[0] = q * fvec3(0,r,0);
  V[1] = q * fvec3(r,0,0);
  V[2] = q * fvec3(-r,0,0);

  auto commandBuffer = [commandQueue commandBuffer];
  auto renderPassDescriptor = [MTLRenderPassDescriptor renderPassDescriptor];
  renderPassDescriptor.colorAttachments[0].texture = drawable.texture;
  renderPassDescriptor.colorAttachments[0].loadAction = MTLLoadActionClear;
  renderPassDescriptor.colorAttachments[0].clearColor =
      MTLClearColorMake(R, G, B, 1.0);

  auto renderEncoder =
      [commandBuffer renderCommandEncoderWithDescriptor:renderPassDescriptor];
  [renderEncoder setRenderPipelineState:pipeline];
  [renderEncoder setVertexBytes:V
                         length:sizeof(fvec3)*3
                        atIndex:0];
  [renderEncoder drawPrimitives:MTLPrimitiveTypeTriangle
                    vertexStart:0
                    vertexCount:3];
  [renderEncoder endEncoding];

  [commandBuffer presentDrawable:drawable];
  [commandBuffer commit];
}
} // namespace

///////////////////////////////////////////////////////////////////////////////

@interface TestBedAppDelegate : NSObject <UIApplicationDelegate> {
  UIWindow *window;
  id<MTLDevice> device;
  id<MTLCommandQueue> commandQueue;
  CAMetalLayer *metalLayer;
  UIViewController *viewController;
  CADisplayLink *displayLink;
  mtl_fn_t _fnVertex, _fnFragment;
  mtl_lib_t _library;
  mtl_pipe_t _pipeline;
  MTLPixelFormat _pixelFormat;
}
@end

///////////////////////////////////////////////////////////////////////////////

@implementation TestBedAppDelegate

///////////////////////////////////////////////////////////////////////////////

- (void)drawFrame {
  auto drawable = [metalLayer nextDrawable];
  renderTriangle(device, commandQueue, drawable, _pipeline);
}

///////////////////////////////////////////////////////////////////////////////

- (void)setupMetal {
  device = MTLCreateSystemDefaultDevice();
  commandQueue = [device newCommandQueue];
  metalLayer = [CAMetalLayer layer];
  metalLayer.device = device;
  metalLayer.pixelFormat = MTLPixelFormatBGRA8Unorm;
  metalLayer.framebufferOnly = YES;
  metalLayer.frame = window.bounds;
  [window.layer addSublayer:metalLayer];

  auto vtx_as_nsstr = nsstrfromstr(vertexShaderSource);
  auto frg_as_nsstr = nsstrfromstr(fragmentShaderSource);

  MTLCompileOptions *options = [MTLCompileOptions new];
  NSError *error = nil;

  _library = [device
      newLibraryWithSource:[NSString stringWithFormat:@"%@\n%@", vtx_as_nsstr,
                                                      frg_as_nsstr]
                   options:options
                     error:&error];

  if (!_library) {
    NSLog(@"Failed to create library: %@", error);
    return 1;
  }

  _fnVertex = [_library newFunctionWithName:@"vertexShader"];
  _fnFragment = [_library newFunctionWithName:@"fragmentShader"];

  assert(_fnVertex && _fnFragment);

  auto drawable = [metalLayer nextDrawable];
  auto pixelFormat = drawable.texture.pixelFormat;
  // Create a vertex descriptor
  MTLVertexDescriptor *vertexDescriptor = [[MTLVertexDescriptor alloc] init];
  vertexDescriptor.attributes[0].format = MTLVertexFormatFloat3;
  vertexDescriptor.attributes[0].offset = 0;
  vertexDescriptor.attributes[0].bufferIndex = 0;
  vertexDescriptor.layouts[0].stride = sizeof(fvec3);
  vertexDescriptor.layouts[0].stepFunction = MTLVertexStepFunctionPerVertex;

  auto pipelineDescriptor = [[MTLRenderPipelineDescriptor alloc] init];
  pipelineDescriptor.vertexFunction = _fnVertex;
  pipelineDescriptor.fragmentFunction = _fnFragment;
  pipelineDescriptor.colorAttachments[0].pixelFormat = pixelFormat;
  pipelineDescriptor.vertexDescriptor = vertexDescriptor;

  _pipeline = [device newRenderPipelineStateWithDescriptor:pipelineDescriptor
                                                     error:&error];
  if (!_pipeline) {
    NSLog(@"Failed to create pipeline state: %@", error);
    assert(false);
  }

  displayLink = [CADisplayLink displayLinkWithTarget:self
                                            selector:@selector(drawFrame)];
  [displayLink addToRunLoop:[NSRunLoop mainRunLoop]
                    forMode:NSDefaultRunLoopMode];
}

///////////////////////////////////////////////////////////////////////////////

- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {

  window = [[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]];
  window.backgroundColor = [UIColor blackColor];

  viewController = [[UIViewController alloc] init];
  viewController.view.backgroundColor = [UIColor blackColor];
  window.rootViewController = viewController;

  [window makeKeyAndVisible];
  [self setupMetal];
  return YES;
}

///////////////////////////////////////////////////////////////////////////////

- (void)applicationWillTerminate:(UIApplication *)application {
  [displayLink invalidate];
}

///////////////////////////////////////////////////////////////////////////////

- (void)applicationDidEnterBackground:(UIApplication *)application {
  [displayLink invalidate];
}

@end

///////////////////////////////////////////////////////////////////////////////

int main(int argc, char *argv[]) {
  @autoreleasepool {
    DLL::a_function();
    int retVal = UIApplicationMain(argc, argv, nil, @"TestBedAppDelegate");
    return retVal;
  }
}
