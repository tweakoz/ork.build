#import <UIKit/UIKit.h>
#import <Metal/Metal.h>
#import <QuartzCore/QuartzCore.h>
#include <boost/filesystem.hpp>
#include <parsertl/parse.hpp>

#define IS_IPHONE (UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone)

// C++ code for rendering the triangle
namespace {
    struct Vertex {
        float position[2];
    };

    const Vertex triangleVertices[] = {
        { {  0.0f,  0.5f } },
        { { -0.5f, -0.5f } },
        { {  0.5f, -0.5f } }
    };

    void renderTriangle(id<MTLDevice> device, id<MTLCommandQueue> commandQueue, id<CAMetalDrawable> drawable) {

        static float phi = 0.0f;
        phi += 0.03f;
        /*
        id<MTLLibrary> defaultLibrary = [device newDefaultLibrary];
        id<MTLFunction> vertexFunction = [defaultLibrary newFunctionWithName:@"vertexShader"];
        id<MTLFunction> fragmentFunction = [defaultLibrary newFunctionWithName:@"fragmentShader"];

        MTLRenderPipelineDescriptor *pipelineDescriptor = [[MTLRenderPipelineDescriptor alloc] init];
        pipelineDescriptor.vertexFunction = vertexFunction;
        pipelineDescriptor.fragmentFunction = fragmentFunction;
        pipelineDescriptor.colorAttachments[0].pixelFormat = drawable.texture.pixelFormat;

        NSError *error = nil;
        id<MTLRenderPipelineState> pipelineState = [device newRenderPipelineStateWithDescriptor:pipelineDescriptor error:&error];
        if (!pipelineState) {
            NSLog(@"Failed to create pipeline state: %@", error);
            return;
        }
        */

       float R = 0.5f*(sinf(phi*0.5f) + 1.0f);
       float G = 0.5f*(sinf(phi*0.7f) + 1.0f);
       float B = 0.5f*(sinf(phi*0.9f) + 1.0f);

        id<MTLCommandBuffer> commandBuffer = [commandQueue commandBuffer];
        MTLRenderPassDescriptor *renderPassDescriptor = [MTLRenderPassDescriptor renderPassDescriptor];
        renderPassDescriptor.colorAttachments[0].texture = drawable.texture;
        renderPassDescriptor.colorAttachments[0].loadAction = MTLLoadActionClear;
        renderPassDescriptor.colorAttachments[0].clearColor = MTLClearColorMake(R,G,B, 1.0);

        id<MTLRenderCommandEncoder> renderEncoder = [commandBuffer renderCommandEncoderWithDescriptor:renderPassDescriptor];
        //[renderEncoder setRenderPipelineState:pipelineState];
        //[renderEncoder setVertexBytes:triangleVertices length:sizeof(triangleVertices) atIndex:0];
        //[renderEncoder drawPrimitives:MTLPrimitiveTypeTriangle vertexStart:0 vertexCount:3];
        [renderEncoder endEncoding];

        [commandBuffer presentDrawable:drawable];
        [commandBuffer commit];
    }
}

@interface TestBedAppDelegate : NSObject <UIApplicationDelegate> {
    UIWindow *window;
    id<MTLDevice> device;
    id<MTLCommandQueue> commandQueue;
    CAMetalLayer *metalLayer;
    UIViewController *viewController;
    CADisplayLink *displayLink;
}
@end

@implementation TestBedAppDelegate

- (void)drawFrame {
    id<CAMetalDrawable> drawable = [metalLayer nextDrawable];
    renderTriangle(device, commandQueue, drawable);
}

- (void)setupMetal {
    device = MTLCreateSystemDefaultDevice();
    commandQueue = [device newCommandQueue];
    metalLayer = [CAMetalLayer layer];
    metalLayer.device = device;
    metalLayer.pixelFormat = MTLPixelFormatBGRA8Unorm;
    metalLayer.framebufferOnly = YES;
    metalLayer.frame = window.bounds;
    [window.layer addSublayer:metalLayer];
    
    [self drawFrame];

    displayLink = [CADisplayLink displayLinkWithTarget:self selector:@selector(drawFrame)];
    [displayLink addToRunLoop:[NSRunLoop mainRunLoop] forMode:NSDefaultRunLoopMode];

}

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {
    window = [[UIWindow alloc] initWithFrame: [[UIScreen mainScreen] bounds]];
    window.backgroundColor = [UIColor blackColor];

   
   viewController = [[UIViewController alloc] init];
   viewController.view.backgroundColor = [UIColor blackColor];
   window.rootViewController = viewController;
   

    [window makeKeyAndVisible];
    [self setupMetal];
    return YES;
}

- (void)applicationWillTerminate:(UIApplication *)application {
    [displayLink invalidate];
}

- (void)applicationDidEnterBackground:(UIApplication *)application {
    [displayLink invalidate];
}

@end

// Metal shader functions
NSString *vertexShaderSource = @"                                          \
    #include <metal_stdlib>                                                \
    using namespace metal;                                                 \
                                                                           \
    struct VertexIn {                                                      \
        float2 position [[attribute(0)]];                                  \
    };                                                                     \
                                                                           \
    vertex float4 vertexShader(VertexIn in [[stage_in]]) {                 \
        return float4(in.position, 0.0, 1.0);                              \
    }                                                                      \
";

NSString *fragmentShaderSource = @"                                        \
    #include <metal_stdlib>                                                \
    using namespace metal;                                                 \
                                                                           \
    fragment float4 fragmentShader() {                                     \
        return float4(1.0, 0.0, 0.0, 1.0);                                 \
    }                                                                      \
";

using mtlx_t = MTLFunctionConstantValues * _Nonnull;
int main(int argc, char *argv[]) {
    @autoreleasepool {

        NSError *error = nil;
        id<MTLDevice> device = MTLCreateSystemDefaultDevice();
        
        MTLCompileOptions *options = [MTLCompileOptions new];
        id<MTLLibrary> library = [device newLibraryWithSource:
            [NSString stringWithFormat:@"%@\n%@", vertexShaderSource, fragmentShaderSource]
            options:options
            error:&error];
        
        if (!library) {
            NSLog(@"Failed to create library: %@", error);
             return 1;
        }
        /*
        id<MTLFunction> vertexFunction = [library newFunctionWithName:@"vertexShader"];
        id<MTLFunction> fragmentFunction = [library newFunctionWithName:@"fragmentShader"];
        
        if (!vertexFunction || !fragmentFunction) {
            NSLog(@"Failed to create shader functions");
            return 1;
        }*/

        int retVal = UIApplicationMain(argc, argv, nil, @"TestBedAppDelegate");
        return retVal;
    }
}