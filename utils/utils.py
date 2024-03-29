import os

def path2tuple(path):
    '''    
    recursively call os.path.split 
    return path components as tuple, preserving hierarchical order

    >>> newdir = r'C:\\temp\\subdir0\\subdir1\\subdir2'
    >>> path2tuple(newdir)
    ('C:\\', 'temp', 'subdir0', 'subdir1', 'suubdir2')
          

    '''
    (a,b) = os.path.split(path)
    if b == '':
        return a,
    else:
        return *path2tuple(a), b

def mkpath(path):
    '''
    Similar to os.mkdir except mkpath also creates implied directory structure as needed.

    For example, suppose the directory "C:\\temp" is empty. Build the hierarchy "C:\\temp\\subdir0\\subdir1\\subdir2" with single call:
    >>> newdir = r'C:\\temp\\subdir0\\subdir1\\subdir2'
    >>> mkpath(newdir)        

    '''
    u = list(path2tuple(path))    
    pth=u[0]

    for i,j in enumerate(u, 1):
        if i < len(u):
            pth = os.path.join(pth,u[i])
            if not any([os.path.isdir(pth), os.path.isfile(pth)]):
                os.mkdir(pth)