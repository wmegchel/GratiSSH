# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

icons = [
         ('icons/add_connection_normal_32px.png', 'icons'),
         ('icons/network_connected_32px.png', 'icons'),
         ('icons/network_disconnected_32px.png', 'icons'),
         ('icons/edit_connection_normal_32px.png', 'icons'),
         ('icons/delete_connection_normal_32px.png', 'icons'),
         ('icons/info_32px.png', 'icons'),
         ('icons/help_32px.png', 'icons'),
         ('icons/add_job_disabled.png', 'icons'),
         ('icons/add_job_normal.png', 'icons'),
         ('icons/add_job_hot.png', 'icons'),
         ('icons/delete_jobs_disabled.png', 'icons'),
         ('icons/delete_jobs_normal.png', 'icons'),
         ('icons/delete_jobs_hot.png', 'icons'),
         ('icons/sync_jobs_disabled.png', 'icons'),
         ('icons/sync_jobs_normal.png', 'icons'),
         ('icons/sync_jobs_hot.png', 'icons'),
         ('icons/rserver_24px.png', 'icons'),
         ('icons/jupyterlab_24px.png', 'icons'),
         ('icons/weblink_32px.png', 'icons'),
         ('icons/stopwatch_24px.png', 'icons'),
         ('icons/weblink_32px.png', 'icons')
         ]

a = Analysis(['hpc_main_ui.py'],
             pathex=['/home/wmegchel/ownCloud/Tools/PyQt5'],
             binaries=[],
             datas=icons,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='HPC-IT',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
