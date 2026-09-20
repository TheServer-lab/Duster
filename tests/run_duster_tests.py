# Deterministic end-to-end tests for Duster written entirely in Fly
import http.server
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile

def norm(out):
    return out.replace("\r\n", "\n").strip()

def run_tests():
    if len(sys.argv) != 3:
        sys.exit("usage: run_duster_tests.py <fly-cc> <duster-root>")

    FLY_CC = os.path.abspath(sys.argv[1])
    DUSTER_ROOT = os.path.abspath(sys.argv[2])

    tmp = tempfile.mkdtemp(prefix="duster-test-")
    server = None
    server_thread = None
    try:
        shutil.copytree(DUSTER_ROOT, tmp, dirs_exist_ok=True)

        serve_root = os.path.join(tmp, "serve")
        release_root = os.path.join(serve_root, "RELEASE")
        offline_root = os.path.join(tmp, "RELEASES")
        os.makedirs(serve_root, exist_ok=True)
        os.makedirs(release_root, exist_ok=True)
        os.makedirs(offline_root, exist_ok=True)

        with open(os.path.join(tmp, "reg.sleep"), "rb") as f:
            reg_content = f.read()
        with open(os.path.join(serve_root, "reg.sleep"), "wb") as f:
            f.write(reg_content)

        c_src_path = os.path.join(tmp, "setup.c")
        setup_exe_path = os.path.join(tmp, "setup.exe")
        with open(c_src_path, "w") as f:
            f.write("int main() { return 0; }\n")
        cc_res = subprocess.run(["gcc", c_src_path, "-o", setup_exe_path], capture_output=True)
        if cc_res.returncode != 0:
            with open(setup_exe_path, "wb") as f:
                f.write(b"MZ" + b"\x00" * 100)

        zip_path = os.path.join(tmp, "kdenlive-v-25.08.1.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            zf.write(setup_exe_path, "setup.exe")
        shutil.copy2(zip_path, os.path.join(release_root, "kdenlive-v-25.08.1.zip"))
        shutil.copy2(zip_path, os.path.join(offline_root, "kdenlive-v-25.08.1.zip"))

        greenshot_zip = os.path.join(release_root, "Greenshot-INSTALLER-1.3.315-RELEASE.zip")
        with zipfile.ZipFile(greenshot_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(setup_exe_path, "setup.exe")

        for app_zip_name in ["nsisapp-1.0.0.zip", "msiapp-1.0.0.zip", "isapp-1.0.0.zip", "7z26.03-x64.zip"]:
            app_zip = os.path.join(release_root, app_zip_name)
            with zipfile.ZipFile(app_zip, "w", zipfile.ZIP_STORED) as zf:
                zf.write(setup_exe_path, "7z2603-x64.exe" if "7z" in app_zip_name else "setup.exe")

        class DusterHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=serve_root, **kwargs)
            def log_message(self, fmt, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), DusterHandler)
        base_url = f"http://127.0.0.1:{server.server_port}"
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        src = os.path.join(tmp, "src", "main.fly")
        out_exe = os.path.join(tmp, "duster" + (".exe" if os.name == "nt" else ""))

        env = os.environ.copy()
        env["DUSTER_RELEASE_BASE"] = base_url + "/RELEASE"
        env["DUSTER_REGISTRY_URL"] = base_url + "/reg.sleep"
        env["FLY_STDLIB_DIR"] = os.path.abspath(os.path.join(DUSTER_ROOT, "..", "stdlib"))

        p = subprocess.run([FLY_CC, src, "-o", out_exe], capture_output=True, cwd=tmp, env=env)
        if p.returncode != 0:
            sys.exit(f"FAIL: Duster compilation failed rc={p.returncode}\nstdout:\n{p.stdout.decode()}\nstderr:\n{p.stderr.decode()}")
        print(f"out_exe exists: {os.path.exists(out_exe)}")

        # Scenario A: remote download + install + cleanup of the archive.
        res = subprocess.run([out_exe, "install", "kdenlive"], capture_output=True, cwd=tmp, env=env)
        stdout = norm(res.stdout.decode())
        if res.returncode != 0:
            sys.exit(f"FAIL: duster install kdenlive exited rc={res.returncode}\nstderr: {res.stderr.decode()}\nstdout: {stdout}")
        if "successfully installed kdenlive" not in stdout:
            sys.exit(f"FAIL: unexpected stdout:\n{stdout}")
        if os.path.exists(os.path.join(tmp, "kdenlive-v-25.08.1.zip")):
            sys.exit("FAIL: downloaded archive was not cleaned up after install")
        if os.path.exists(os.path.join(tmp, "extracted_kdenlive")):
            sys.exit("FAIL: extracted directory was not cleaned up after install")
        print("ok [duster_remote_download_install]")

        # Scenario B: unknown application -> registry error, nonzero exit.
        res_unk = subprocess.run([out_exe, "install", "nonexistent"], capture_output=True, cwd=tmp, env=env)
        if res_unk.returncode == 0:
            sys.exit("FAIL: expected nonzero exit for unknown application")
        print("ok [duster_unknown_app_error]")

        # Scenario C: -keep retains the downloaded archive and extracted directory.
        res_keep = subprocess.run([out_exe, "install", "kdenlive-keep"], capture_output=True, cwd=tmp, env=env)
        if res_keep.returncode != 0:
            sys.exit(f"FAIL: duster install kdenlive-keep failed: {res_keep.stderr.decode()}")
        if not os.path.exists(os.path.join(tmp, "kdenlive-v-25.08.1.zip")):
            sys.exit("FAIL: -keep flag failed to retain archive")
        if not os.path.exists(os.path.join(tmp, "extracted_kdenlive")):
            sys.exit("FAIL: -keep flag failed to retain extracted directory")
        print("ok [duster_install_keep]")

        # Scenario D: registered app whose artifact is missing on the release
        # server -> HTTP 404 surfaces as a catchable duster error.
        res_404 = subprocess.run([out_exe, "install", "phantom"], capture_output=True, cwd=tmp, env=env)
        if res_404.returncode == 0:
            sys.exit("FAIL: expected nonzero exit when artifact 404s")
        err_text = res_404.stderr.decode() + res_404.stdout.decode()
        if "404" not in err_text:
            sys.exit(f"FAIL: expected HTTP 404 error, got:\n{err_text}")
        print("ok [duster_http_404_error]")

        # Scenario E: Greenshot dynamic-Huffman deflate extraction test.
        res_gs = subprocess.run([out_exe, "install", "greenshot"], capture_output=True, cwd=tmp, env=env)
        stdout_gs = norm(res_gs.stdout.decode())
        if res_gs.returncode != 0:
            sys.exit(f"FAIL: duster install greenshot exited rc={res_gs.returncode}\nstderr: {res_gs.stderr.decode()}\nstdout: {stdout_gs}")
        if "successfully installed greenshot" not in stdout_gs:
            sys.exit(f"FAIL: unexpected stdout for greenshot:\n{stdout_gs}")
        print("ok [duster_greenshot_dynamic_huffman]")

        # Scenario F: duster list and duster search
        res_list = subprocess.run([out_exe, "list"], capture_output=True, cwd=tmp, env=env)
        stdout_list = norm(res_list.stdout.decode())
        if res_list.returncode != 0 or "kdenlive" not in stdout_list:
            sys.exit(f"FAIL: duster list failed or missing kdenlive:\n{stdout_list}")
        print("ok [duster_list]")

        res_search = subprocess.run([out_exe, "search", "greenshot"], capture_output=True, cwd=tmp, env=env)
        stdout_search = norm(res_search.stdout.decode())
        if res_search.returncode != 0 or "Greenshot" not in stdout_search:
            sys.exit(f"FAIL: duster search failed:\n{stdout_search}")
        print("ok [duster_search]")

        # Scenario G: duster uninstall
        gs_reg_key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\Greenshot_is1"
        subprocess.run(["reg", "add", gs_reg_key, "/f"], capture_output=True)
        subprocess.run(["reg", "add", gs_reg_key, "/v", "DisplayName", "/t", "REG_SZ", "/d", "Greenshot 1.3.315", "/f"], capture_output=True)
        subprocess.run(["reg", "add", gs_reg_key, "/v", "UninstallString", "/t", "REG_SZ", "/d", "cmd.exe /c exit 0", "/f"], capture_output=True)

        res_uninst = subprocess.run([out_exe, "uninstall", "greenshot"], capture_output=True, cwd=tmp, env=env)
        subprocess.run(["reg", "delete", gs_reg_key, "/f"], capture_output=True)

        if res_uninst.returncode != 0:
            sys.exit(f"FAIL: duster uninstall greenshot failed rc={res_uninst.returncode}\nstdout:\n{res_uninst.stdout.decode()}\nstderr:\n{res_uninst.stderr.decode()}")
        res_list2 = subprocess.run([out_exe, "list"], capture_output=True, cwd=tmp, env=env)
        if "greenshot" in norm(res_list2.stdout.decode()).lower():
            sys.exit("FAIL: greenshot still present in list after uninstall")
        print("ok [duster_uninstall]")

        # Scenario H: SHA256 mismatch failure test
        bad_reg_path = os.path.join(serve_root, "reg.sleep")
        with open(bad_reg_path, "a", encoding="utf-8") as f:
            f.write("\npackage\n  name badpkg\n  license OpenSource\n  version \"1.0.0\"\n  installer_type Inno\n  verification_hash SHA256\n  file_hash \"deadbeef00000000000000000000000000000000000000000000000000000000\"\n  category coll [Bad]\n  file_name \"kdenlive-v-25.08.1.zip\"\n")
        with open(bad_reg_path, "rb") as f:
            with open(os.path.join(tmp, "reg.sleep"), "wb") as f2:
                f2.write(f.read())

        res_hash = subprocess.run([out_exe, "install", "badpkg"], capture_output=True, cwd=tmp, env=env)
        if res_hash.returncode == 0:
            sys.exit("FAIL: expected nonzero exit for SHA256 mismatch")
        print("ok [duster_sha256_mismatch_abort]")

        # Scenario I: installer types (NSIS, MSI, InstallShield, Exe)
        for app in ["nsisapp", "msiapp", "isapp", "7zip"]:
            res_app = subprocess.run([out_exe, "install", app], capture_output=True, cwd=tmp, env=env)
            if res_app.returncode != 0:
                sys.exit(f"FAIL: duster install {app} failed rc={res_app.returncode}\nstdout:\n{res_app.stdout.decode()}\nstderr:\n{res_app.stderr.decode()}")
        print("ok [duster_installer_types]")

        # Scenario J: Windows uninstall registry integration tests
        reg_key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\RegTestApp_is1"
        subprocess.run(["reg", "add", reg_key, "/f"], capture_output=True)
        subprocess.run(["reg", "add", reg_key, "/v", "DisplayName", "/t", "REG_SZ", "/d", "RegTestApp 1.0.0", "/f"], capture_output=True)
        subprocess.run(["reg", "add", reg_key, "/v", "UninstallString", "/t", "REG_SZ", "/d", "cmd.exe /c exit 1", "/f"], capture_output=True)
        subprocess.run(["reg", "add", reg_key, "/v", "QuietUninstallString", "/t", "REG_SZ", "/d", "cmd.exe /c exit 0", "/f"], capture_output=True)

        with open(os.path.join(tmp, "list.txt"), "a", encoding="utf-8") as f:
            f.write("RegTestApp|1.0.0\n")

        res_reg_uninst = subprocess.run([out_exe, "uninstall", "regtestapp"], capture_output=True, cwd=tmp, env=env)
        if res_reg_uninst.returncode != 0:
            sys.exit(f"FAIL: uninstall regtestapp failed rc={res_reg_uninst.returncode}\nstdout:\n{res_reg_uninst.stdout.decode()}\nstderr:\n{res_reg_uninst.stderr.decode()}")
        print("ok [duster_uninstall_registry_quiet]")

        subprocess.run(["reg", "add", reg_key, "/v", "QuietUninstallString", "/t", "REG_SZ", "/d", "cmd.exe /c exit 1", "/f"], capture_output=True)
        with open(os.path.join(tmp, "list.txt"), "a", encoding="utf-8") as f:
            f.write("RegTestApp|1.0.0\n")
        res_fail_uninst = subprocess.run([out_exe, "uninstall", "regtestapp"], capture_output=True, cwd=tmp, env=env)
        if res_fail_uninst.returncode == 0:
            sys.exit("FAIL: expected nonzero exit for failing uninstaller")
        with open(os.path.join(tmp, "list.txt"), "r", encoding="utf-8") as f:
            list_content = f.read()
        if "RegTestApp" not in list_content:
            sys.exit("FAIL: failed uninstaller removed entry from list.txt")
        print("ok [duster_uninstall_failure_keeps_list]")

        subprocess.run(["reg", "delete", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\RegTestApp_is1", "/f"], capture_output=True)

        # Test command string parsing variations
        reg_key2 = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\RegTestApp2_is1"
        subprocess.run(["reg", "add", reg_key2, "/f"], capture_output=True)
        subprocess.run(["reg", "add", reg_key2, "/v", "DisplayName", "/t", "REG_SZ", "/d", "RegTestApp2 1.0.0", "/f"], capture_output=True)
        subprocess.run(["reg", "add", reg_key2, "/v", "UninstallString", "/t", "REG_SZ", "/d", "cmd.exe /c exit 0", "/f"], capture_output=True)

        with open(os.path.join(tmp, "list.txt"), "a", encoding="utf-8") as f:
            f.write("RegTestApp2|1.0.0\n")

        res_reg_uninst2 = subprocess.run([out_exe, "uninstall", "regtestapp2"], capture_output=True, cwd=tmp, env=env)
        if res_reg_uninst2.returncode != 0:
            sys.exit(f"FAIL: uninstall regtestapp2 failed rc={res_reg_uninst2.returncode}\nstdout:\n{res_reg_uninst2.stdout.decode()}\nstderr:\n{res_reg_uninst2.stderr.decode()}")
        print("ok [duster_uninstall_command_parsing]")
        subprocess.run(["reg", "delete", reg_key2, "/f"], capture_output=True)

        print("duster: all tests passed successfully")
    finally:
        if server:
            server.shutdown()
            server.server_close()
        if server_thread:
            server_thread.join(timeout=10)
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    run_tests()
