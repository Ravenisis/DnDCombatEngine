from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_inno_setup_script_targets_packaged_executable() -> None:
    script = (PROJECT_ROOT / "packaging" / "DnDCombatEngine.iss").read_text(encoding="utf-8")

    assert 'OutputBaseFilename=DnDCombatEngine-{#MyAppVersion}-Setup' in script
    assert "SetupIconFile=..\\src\\dnd_combat_engine\\data\\app_icon.ico" in script
    assert 'Source: "..\\dist\\DnDCombatEngine\\*"' in script
    assert 'Filename: "{app}\\{#MyAppExeName}"' in script
    assert "IconFilename:" in script


def test_installer_build_script_invokes_inno_setup() -> None:
    script = (PROJECT_ROOT / "scripts" / "build_installer.ps1").read_text(encoding="utf-8")

    assert "build_windows.ps1" in script
    assert "ISCC.exe" in script
    assert "DnDCombatEngine.iss" in script


def test_msi_script_defines_product_shortcut_and_harvested_files() -> None:
    script = (PROJECT_ROOT / "packaging" / "DnDCombatEngine.wxs").read_text(encoding="utf-8")

    assert 'Name="DnDCombatEngine"' in script
    assert 'ComponentGroupRef Id="ApplicationFiles"' in script
    assert 'Target="[INSTALLFOLDER]DnDCombatEngine.exe"' in script
    assert 'Icon Id="AppIcon.ico"' in script
    assert 'Icon="AppIcon.ico"' in script


def test_pyinstaller_spec_sets_windows_icon() -> None:
    script = (PROJECT_ROOT / "packaging" / "DnDCombatEngine.spec").read_text(
        encoding="utf-8"
    )

    assert "app_icon.ico" in script
    assert "icon=str(app_icon)" in script


def test_msi_build_script_harvests_pyinstaller_output() -> None:
    script = (PROJECT_ROOT / "scripts" / "build_msi.ps1").read_text(encoding="utf-8")

    assert "build_windows.ps1" in script
    assert "wix.exe" in script
    assert "ApplicationFiles.wxs" in script
    assert "ComponentGroup" in script
    assert 'ProjectRoot=$ProjectRoot' in script
    assert "DnDCombatEngine-1.0.0-x64.msi" in script


def test_package_workflow_builds_distributions_executable_and_installer() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "package.yml").read_text(
        encoding="utf-8"
    )

    assert "python -m build" in workflow
    assert ".\\scripts\\build_windows.ps1 -SkipInstall" in workflow
    assert ".\\scripts\\build_installer.ps1 -SkipExecutableBuild" in workflow
    assert ".\\scripts\\build_msi.ps1 -SkipExecutableBuild" in workflow
    assert "DnDCombatEngine-installer" in workflow
    assert "DnDCombatEngine-msi" in workflow
