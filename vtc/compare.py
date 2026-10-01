"""Byte comparison of scientific artifacts across deterministic reruns."""
import argparse
import hashlib
from pathlib import Path

FILES=('cases.csv','assertions.jsonl','traces.jsonl','inputs.json','summary.json')


def compare(a,b):
    result={}
    for name in FILES:
        left,right=(Path(a)/name).read_bytes(),(Path(b)/name).read_bytes()
        if left!=right: raise AssertionError(f'different scientific artifact: {name}')
        result[name]=hashlib.sha256(left).hexdigest()
    print('PASS: five scientific artifacts byte-identical')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('left');p.add_argument('right')
    args=p.parse_args();compare(args.left,args.right)
