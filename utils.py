import os
import os.path as osp
import uuid
import shutil

class TempFolder:

    def __enter__(self):
        folder_name = str(uuid.uuid4())
        self.root = osp.abspath(osp.join('tmp', folder_name))
        os.makedirs(self.root)

        sharedDataFolder = 'sharedData'
        os.symlink(osp.abspath(sharedDataFolder), osp.abspath(osp.join(self.root, sharedDataFolder)))

        self.cwd = os.getcwd()
        #os.chdir(osp.abspath(self.root))
        
        return self

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.root)
        #os.chdir(self.cwd)
        pass