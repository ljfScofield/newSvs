# -*- mode: python -*-

block_cipher = pyi_crypto.PyiBlockCipher(key='ChangeCipherSp.c')


a = Analysis(['main.py'],
             pathex=['D:\\XHSVSClient'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='SVS',
          debug=False,
          strip=False,
          upx=True,
          console=False , version='versionfile.py', icon='xinghan.ico')
