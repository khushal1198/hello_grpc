load("@my_pip_deps//:requirements.bzl", "requirement")

py_binary(
    name = "hello_world",
    srcs = ["main.py"],
    main = "main.py",
    deps = [
        requirement("requests"),
    ],
) 