#!/usr/bin/env python3
"""招投标数据自动提交+推送（run.sh 招投标段收尾用，launchd 定时调用）。

只提交白名单内的招投标数据文件；git push 失败（本机 git HTTPS 通道常 502）
自动降级走 Git Data API（api.github.com 走代理可达）。幂等：白名单文件与
远端 main 完全一致时不产生提交。兼容系统 python3 3.9。

用法: python3 scripts/bids-autopush.py [--dry-run]
"""
import base64
import json
import subprocess
import sys
import time

REPO = 'xiewengi/EDUima'
BRANCH = 'main'
# 白名单：招投标链路产物。新增文件放 data/_raw/bids-md/ 自动纳入。
WHITELIST_FILES = [
    'public/data/bidding.json',
    'data/_raw/ima-bids.json',
    'data/_raw/bids-award-info.json',
    'data/_raw/bids-source-urls.json',
]
WHITELIST_DIRS = ['data/_raw/bids-md']
DRY_RUN = '--dry-run' in sys.argv


def log(msg):
    print('[bids-autopush] %s' % msg)


def git(args, inp=None):
    return subprocess.run(['git'] + args, capture_output=True, text=True, input=inp)


def cred_token():
    r = git(['credential', 'fill'], 'protocol=https\nhost=github.com\n\n')
    for line in r.stdout.splitlines():
        if line.startswith('password='):
            return line.split('=', 1)[1]
    return ''


TOKEN = cred_token()


def api(method, url, payload=None):
    cmd = ['curl', '-sS', '-X', method,
           '-H', 'Authorization: Bearer %s' % TOKEN,
           '-H', 'Accept: application/vnd.github+json']
    data_file = None
    if payload is not None:
        # 大 blob 的 base64 走 argv 会超 macOS ARG_MAX，必须 -d @file
        import tempfile
        data_file = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
        json.dump(payload, data_file, ensure_ascii=False)
        data_file.close()
        cmd += ['-d', '@%s' % data_file.name]
    cmd.append('https://api.github.com/repos/%s/%s' % (REPO, url))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if data_file:
        import os
        os.unlink(data_file.name)
    if r.returncode != 0:
        raise RuntimeError('curl 失败: %s' % r.stderr.strip())
    d = json.loads(r.stdout)
    if isinstance(d, dict) and d.get('message') and 'sha' not in d:
        raise RuntimeError('API %s %s: %s' % (method, url, d['message']))
    return d


def local_blob_sha(path):
    """git blob sha（纯本地计算，不依赖网络/索引）"""
    r = git(['hash-object', path])
    return r.stdout.strip() if r.returncode == 0 else None


def collect_local():
    """白名单 → {path: blob_sha 或 None(删除)}；目录扫实际文件（含未跟踪新增）"""
    m = {}
    for f in WHITELIST_FILES:
        m[f] = local_blob_sha(f)
    for d in WHITELIST_DIRS:
        r = git(['ls-files', '-z', '--', d])
        known = set(p for p in r.stdout.split('\0') if p)
        # 目录下实际存在的文件（含未跟踪的）
        r2 = git(['ls-files', '-z', '--others', '--cached', '--exclude-standard', '--', d])
        for p in (x for x in r2.stdout.split('\0') if x):
            m[p] = local_blob_sha(p)
        # 已被 git 跟踪但磁盘上已删除的 → 标记远端删除
        for p in known:
            if p not in m:
                m[p] = None
    return m


def get_remote_tree(ref_sha):
    """远端 main 全量 {path: blob_sha}（本地缺远端对象时 git rev-parse 不可用，必须走 API）"""
    d = api('GET', 'git/trees/%s?recursive=1' % ref_sha)
    m = {e['path']: e['sha'] for e in d.get('tree', []) if e.get('type') == 'blob'}
    if d.get('truncated'):
        log('⚠️ 远端 tree 被截断，退化逐路径比对')
        for p in list(m):
            try:
                m[p] = api('GET', 'contents/%s?ref=%s' % (p, ref_sha))['sha']
            except Exception:
                pass
    return m


def main():
    head_local = git(['rev-parse', 'HEAD']).stdout.strip()
    # 远端最新 commit：git 失败就走 API
    ref_sha = ''
    r = git(['ls-remote', 'origin', BRANCH])
    if r.returncode == 0 and r.stdout.strip():
        ref_sha = r.stdout.split()[0]
    else:
        log('git ls-remote 失败（通道 502?），走 API 查 ref')
        ref_sha = api('GET', 'git/ref/heads/%s' % BRANCH)['object']['sha']
    log('远端 %s = %s' % (BRANCH, ref_sha[:12]))

    local = collect_local()
    remote = get_remote_tree(ref_sha)
    diffs = {}
    for path, sha in local.items():
        if sha != remote.get(path):
            diffs[path] = (sha, remote.get(path))
    if not diffs:
        log('白名单文件与远端一致，无需提交 ✓')
        return 0
    for p, (s, rs) in sorted(diffs.items()):
        log('  变更: %s (%s → %s)' % (p, (rs or '无')[:10], (s or '删除')[:10]))

    if DRY_RUN:
        log('dry-run，不提交')
        return 0

    # 1) 先试 git push（快速失败不拖时间）
    commit_msg = 'chore(bids): 自动同步 ima 招投标数据 %s' % time.strftime('%Y-%m-%d %H:%M')
    git(['add', '-A', '--'] + WHITELIST_FILES + WHITELIST_DIRS)
    c = git(['commit', '-m', commit_msg, '--'] + WHITELIST_FILES + WHITELIST_DIRS)
    if c.returncode != 0:
        log('git commit 失败: %s' % (c.stderr.strip() or c.stdout.strip()))
        return 1
    local_commit = git(['rev-parse', 'HEAD']).stdout.strip()
    log('本地 commit %s，尝试 git push…' % local_commit[:12])
    p = git(['push', 'origin', BRANCH])
    if p.returncode == 0:
        log('git push 成功 ✓')
        return 0
    log('git push 失败（%s），走 Git Data API 兜底' % p.stderr.strip().splitlines()[-1][:60] if p.stderr.strip() else 'git push 失败，走 Git Data API 兜底')

    # 2) API 兜底：blobs → tree(base_tree) → commit → PATCH ref
    base_tree = api('GET', 'git/commits/%s' % ref_sha)['tree']['sha']
    tree = []
    for path in sorted(diffs):
        sha = diffs[path][0]
        if sha is None:
            tree.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': None})
            continue
        body = open(path, 'rb').read()
        b = api('POST', 'git/blobs', {'content': base64.b64encode(body).decode(),
                                      'encoding': 'base64'})
        tree.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': b['sha']})
    new_tree = api('POST', 'git/trees', {'base_tree': base_tree, 'tree': tree})
    ident = {'name': 'xiewengi', 'email': 'xiewengi@users.noreply.github.com'}
    commit = api('POST', 'git/commits', {
        'message': commit_msg,
        'tree': new_tree['sha'],
        'parents': [ref_sha],
        'author': dict(ident),
        'committer': dict(ident),
    })
    api('PATCH', 'git/refs/heads/%s' % BRANCH, {'sha': commit['sha'], 'force': False})
    log('API 推送成功：远端 %s = %s ✓' % (BRANCH, commit['sha'][:12]))
    # 丢弃本地平行 commit（改动退回暂存区），远端已有内容等价提交，避免平行历史越积越多
    r = git(['reset', '--soft', 'HEAD~1'])
    log('本地平行 commit 已退回暂存区' if r.returncode == 0 else '⚠️ reset --soft 失败（不影响远端）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
