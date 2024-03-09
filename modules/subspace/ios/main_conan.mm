#import <UIKit/UIKit.h>
#include <boost/filesystem.hpp>
#include <parsertl/parse.hpp>

// Simple macro distinguishes iPhone from iPad
#define IS_IPHONE (UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone)
@interface TestBedAppDelegate : NSObject <UIApplicationDelegate>
{
    UIWindow *window;
}
@end

@implementation TestBedAppDelegate

- (UIViewController *) helloController {
    UIViewController *vc = [[UIViewController alloc] init];
    vc.view.backgroundColor = [UIColor magentaColor];

    auto dir = boost::filesystem::temp_directory_path();
    auto dir_as_nsstring = [NSString stringWithUTF8String:dir.c_str()];

    // Add a basic label that says "Hello World"
    UILabel *label = [[UILabel alloc] initWithFrame:
        CGRectMake(0.0f, 0.0f, window.bounds.size.width, 80.0f)];
    label.text = dir_as_nsstring;
    label.center = CGPointMake(CGRectGetMidX(window.bounds),
                               CGRectGetMidY(window.bounds));
    label.numberOfLines = 0; // Enable text wrapping
    label.textAlignment = NSTextAlignment(UITextAlignmentCenter);
    label.font = [UIFont boldSystemFontOfSize: IS_IPHONE ? 12.0f : 18.0f];
    label.backgroundColor = [UIColor clearColor];

    [vc.view addSubview:label];

    return vc;
}

- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
{
        window = [[UIWindow alloc] initWithFrame:
        [[UIScreen mainScreen] bounds]];
    window.rootViewController = [self helloController];
    [window makeKeyAndVisible];
    return YES;
}
@end

int main(int argc, char *argv[]) {
        @autoreleasepool {
            int retVal =
            UIApplicationMain(argc, argv, nil, @"TestBedAppDelegate");
        return retVal;
    }
}