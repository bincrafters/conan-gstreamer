#include <iostream>
#include <gst/gst.h>

int main(int argc, char * argv[])
{
    gst_init(&argc, &argv);
    std::cout << "GStreamer version: " << gst_version_string() << std::endl;
    return 0;
}
