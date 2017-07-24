import os
import re
import urllib
import threading
import subprocess
from bs4 import BeautifulSoup


def geturl(url):
    #print('Fetching %s' % url)
    fp = urllib.request.urlopen(url)
    page = fp.read().decode('utf8')
    fp.close()
    return page

def async_process(fun):
    ''' Decorator for running thread '''
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=fun, args=args, kwargs=kwargs)
        t.start()
        return t
    return wrapper

# @Todo
#   * get the number of commit merged from upstream/master.
#   * get the numner of new branch fetched.
#

class GitCommander(object):

    def __init__(self):
        pass

    def extract_forked_repo(self, doc):
        '''
        <span class="fork-flag">
            <span class="text">forked from <a href="/OpenBazaar/OpenBazaar-Client">OpenBazaar/OpenBazaar-Client</a></span>
        </span>
        '''
        soup = BeautifulSoup(doc, 'lxml')
        regex = re.compile('forked from')
        reg_hits = soup.find_all(text = regex)
        if len(reg_hits) == 0:
            return None
        else:
            pick = reg_hits[0]
            repo = pick.find_parent().a['href']
            return repo


    def merge_upstream_all(self):

        #cwd = os.getenv('PWD')

        for _dir in next(os.walk('.'))[1]:
            if not self.is_gitrepo(_dir):
                continue

            self.merge_upstream(_dir)


    @async_process
    def merge_upstream(self, _dir):

        upstream_url = self.get_upstream(_dir)
        if not upstream_url:
            return

        if not self.git_branch(_dir) == 'master':
            self.command('git', '-C', _dir, 'checkout', 'master')

        if not 'upstream' in self.git_remotes(_dir):
            self.command('git', '-C', _dir, 'remote', 'add', 'upstream', upstream_url)

        self.command('git', '-C', _dir, 'fetch', 'upstream')
        self.command('git', '-C', _dir, 'merge', 'upstream/master')
        self.command('git', '-C', _dir, 'push', 'origin', 'master')

        print('%s synced from %s' % (_dir, upstream_url))


    def is_gitrepo(self, _dir):
        isgit =  os.path.isdir(os.path.join(_dir, '.git'))
        return isgit

    def command(self, *args):
        return subprocess.check_output(args).decode('utf8').rstrip('\n')

    def get_origin(self, _dir):
        origin_repo = self.command('git', '-C', _dir, 'config', 'remote.origin.url')

        if origin_repo.startswith('http'):
            url =  origin_repo
        elif origin_repo.startswith('git'):
            uri = origin_repo.split('@')[1].replace(':','/', 1)
            url = 'https://' + uri
        else:
            raise ValueError('unknow URI: %s' % origin_repo)

        return url

    def git_branch(self, _dir):
        git_branch = self.command('git', '-C', _dir, 'rev-parse','--abbrev-ref' ,'HEAD')
        return git_branch

    def git_hash(self, _dir):
        git_branch = self.command('git', '-C', _dir, 'rev-parse', 'HEAD')
        return git_hash

    def git_remotes(self, _dir):
        remotes = self.command('git', '-C', _dir, 'branch', '-r')
        git_remotes = []
        [git_remotes.append(b.split('/')[0]) for b in remotes.split()]
        return set(git_remotes)

    def get_upstream(self, _dir):
        origin_url = self.get_origin(_dir)
        url_obj = urllib.parse.urlparse(origin_url)
        page = geturl(origin_url)
        upstream_repo = self.extract_forked_repo(page)
        if not upstream_repo:
            print('source repo : %s' % origin_url)
            return None
        upstream_url = url_obj.scheme + '://' + url_obj.netloc + upstream_repo
        return upstream_url


if __name__ == '__main__':
    gc = GitCommander()
    gc.merge_upstream_all()
