import fab.fabfile as f
import os
def CreateOrExport(rootpath,subpath,allowedhosts,options):
    path = os.path.join(rootpath,subpath)
    f.unexport_volume(path) # Unexport things for updates
    f.export_volume(path,allowedhosts,options)

def UnExport(path,deletevol = False):
    f.unexport_volume(path)
    if deletevol:
        f.delete_directory(path)


