"""Freeze a reproducible attempt schedule without dispatching agents."""
import argparse
import json
from pathlib import Path
from sanctum_run.agent_schedule import plan_schedule


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    schedule=plan_schedule(args.bundle,args.out)
    print(json.dumps(dict(schedule=str(args.out/'schedule.json'),planned_attempts=len(schedule['attempts']),
                          paid_dispatch=False)))


if __name__=='__main__':main()
