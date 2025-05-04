# Bazel Python Project Example

This project demonstrates how to set up a minimal Python project using Bazel with bzlmod (MODULE.bazel) and pip dependencies.

## Project Structure

```
hello_grpc/
├── BUILD
├── main.py
├── MODULE.bazel
├── requirements.in
├── requirements_lock.txt
```

## Steps to Reproduce

### 1. Create your Python script

```
# main.py
print("Hello World")
```

### 2. Create a minimal `requirements.in` (write this file yourself)

```
requests
```

### 3. Generate a lock file (this will be generated for you)

Install pip-tools if you haven't:
```
python3 -m pip install pip-tools
```

Generate the lock file (this creates `requirements_lock.txt` from your `requirements.in`):
```
pip-compile requirements.in --output-file requirements_lock.txt
```

### 4. Set up Bazel files

#### `MODULE.bazel`
```
bazel_dep(name = "rules_python", version = "0.40.0")

python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(
    python_version = "3.11",
)

pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")
pip.parse(
    hub_name = "my_pip_deps",
    python_version = "3.11",
    requirements_lock = "//:requirements_lock.txt",
)
use_repo(pip, "my_pip_deps")
```

#### `BUILD`
```
load("@my_pip_deps//:requirements.bzl", "requirement")

py_binary(
    name = "hello_world",
    srcs = ["main.py"],
    main = "main.py",
    deps = [
        requirement("requests"),
    ],
)
```

## 5. Run your project

```
bazel run //:hello_world
```

You should see:
```
Hello World
```

---

## Notes
- You can add more dependencies to `requirements.in` and re-run `pip-compile` to update your lock file.
- This setup uses Bazel's bzlmod (MODULE.bazel) for modern Python dependency management.
- If you want to use a different Python version, update both `python_version` fields in `MODULE.bazel` and re-lock your dependencies for that version. 