# Deterministic end-to-end tests for Duster written entirely in Fly
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

def norm(out):
    return out.replace("\r\n", "\n").strip()

def run_tests():
    if len(sys.argv) != 3:
        sys.exit("usage: run_duster_tests.py <fly-cc> <duster-root>")
    
    FLY_CC = os.path.abspath(sys.argv[1])
    DUSTER_ROOT = os.path.abspath(sys.argv[2])

    tmp = tempfile.mkdtemp(prefix="duster-test-")
    try:
        shutil.copytree(DUSTER_ROOT, tmp, dirs_exist_ok=True)

        releases_dir = os.path.join(tmp, "RELEASES")
        os.makedirs(releases_dir, exist_ok=True)

        # Compile a tiny C program into setup.exe so Windows can execute it natively
        c_src_path = os.path.join(tmp, "setup.c")
        setup_exe_path = os.path.join(tmp, "setup.exe")
        with open(c_src_path, "w") as f:
            f.write("int main() { return 0; }\n")
        
        cc_res = subprocess.run(["gcc", c_src_path, "-o", setup_exe_path], capture_output=True)
        if cc_res.returncode != 0:
            # Fallback if gcc not found: python script or similar
            with open(setup_exe_path, "wb") as f:
                f.write(b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 500) # dummy MZ header if needed, but gcc is available in MinGW env
        
        zip_path = os.path.join(releases_dir, "kdenlive-v-25.08.1.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            zf.write(setup_exe_path, "setup.exe")

        src = os.path.join(tmp, "src", "main.fly")
        out_exe = os.path.join(tmp, "duster" + (".exe" if os.name == "nt" else ""))
        
        p = subprocess.run([FLY_CC, src, "-o", out_exe], capture_output=True, cwd=tmp)
        if p.returncode != 0:
            sys.exit(f"FAIL: Duster compilation failed\n{p.stderr.decode()}")

        res = subprocess.run([out_exe, "-install", "kdenlive"], capture_output=True, cwd=tmp)
        stdout = norm(res.stdout.decode())
        if res.returncode != 0:
            sys.exit(f"FAIL: duster -install kdenlive exited rc={res.returncode}\nstderr: {res.stderr.decode()}\nstdout: {stdout}")
        if "successfully installed kdenlive" not in stdout:
            sys.exit(f"FAIL: unexpected stdout:\n{stdout}")
        print("ok [duster_install_kdenlive]")

        res_unk = subprocess.run([out_exe, "-install", "nonexistent"], capture_output=True, cwd=tmp)
        if res_unk.returncode == 0:
            sys.exit("FAIL: expected nonzero exit for unknown application")
        print("ok [duster_unknown_app_error]")

        res_keep = subprocess.run([out_exe, "-install", "kdenlive-keep"], capture_output=True, cwd=tmp)
        if res_keep.returncode != 0:
            sys.exit(f"FAIL: duster -install kdenlive-keep failed: {res_keep.stderr.decode()}")
        if not os.path.exists(os.path.join(tmp, "kdenlive-v-25.08.1.zip")):
            sys.exit("FAIL: -keep flag failed to retain archive")
        print("ok [duster_install_keep]")

        print("duster: all tests passed successfully")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    run_tests()
