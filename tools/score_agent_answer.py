"""Create a blinded judge packet or score saved output; performs no inference."""
import argparse
import json
from pathlib import Path

from sanctum_run.agent_score import judge_packet,score_answer
from sanctum_run.agent_session import write_atomic
from sanctum_run.bundle import validate_bundle


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path)
    parser.add_argument('--task-id',required=True)
    parser.add_argument('--attempt',required=True,type=Path)
    parser.add_argument('--answer',required=True,type=Path)
    parser.add_argument('--review',type=Path)
    parser.add_argument('--quality-policy',type=Path)
    parser.add_argument('--human-acceptance',type=Path)
    parser.add_argument('--judge-packet',action='store_true')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    validate_bundle(args.bundle)
    import yaml
    config=yaml.safe_load(args.bundle.read_text());root=args.bundle.resolve().parent
    gold=next(json.loads(line) for line in (root/config['gold']).read_text().splitlines()
              if json.loads(line)['task_id']==args.task_id)
    corpus=(root/config['corpus']['manifest']).parent
    rows=[]
    for file in sorted((corpus/'hubs').glob('*/artifacts.jsonl')):
        for line in file.read_text().splitlines():
            row=json.loads(line);row['source_id']=file.parent.name;rows.append(row)
    attempt=json.loads(args.attempt.read_text());answer=args.answer.read_text()
    context=None
    if args.quality_policy:
        from sanctum_run.quality_policy import load_policy,scoring_context
        context=scoring_context(load_policy(args.quality_policy),args.task_id)
    if args.judge_packet:
        result=judge_packet(answer,gold,attempt,rows,context)
    else:
        review=json.loads(args.review.read_text()) if args.review else None
        acceptance=json.loads(args.human_acceptance.read_text()) if args.human_acceptance else None
        reviewers=None
        if acceptance:
            import hashlib
            from sanctum_run.bundle import _file
            policy=config.get('scoring',{}).get('human_reviewers')
            if not policy: raise ValueError('human acceptance requires a pinned reviewer registry')
            registry=_file(root,policy['file'])
            if hashlib.sha256(registry.read_bytes()).hexdigest()!=policy['expected_sha256']:
                raise ValueError('human reviewer registry hash mismatch')
            reviewers=json.loads(registry.read_text())
        result=score_answer(answer,gold,attempt,rows,review,human_acceptance=acceptance,human_reviewers=reviewers,context=context)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    write_atomic(args.out,result)
    print(json.dumps(dict(output=str(args.out),task_id=args.task_id,paid_inference=False)))


if __name__=='__main__':
    main()
