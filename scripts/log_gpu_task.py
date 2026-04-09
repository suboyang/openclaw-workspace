#!/usr/bin/env python3
import argparse
import json
import socket
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

DB_PATH = Path('/home/openclaw/.openclaw/workspace/gpu_tasks.db')


def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ''


def get_power_profile():
    out = run_cmd(['powerprofilesctl', 'get'])
    return out or None


def get_gpu_info():
    q = run_cmd([
        'nvidia-smi',
        '--query-gpu=name,pci.bus_id,memory.used,memory.total,utilization.gpu,pcie.link.gen.max,pcie.link.gen.current,pcie.link.width.max,pcie.link.width.current',
        '--format=csv,noheader,nounits'
    ])
    if not q:
        return {}
    first = q.splitlines()[0]
    parts = [p.strip() for p in first.split(',')]
    if len(parts) < 9:
        return {}
    return {
        'gpu_name': parts[0],
        'gpu_bus_id': parts[1],
        'gpu_memory_used_mb': int(parts[2]) if parts[2].isdigit() else None,
        'gpu_memory_total_mb': int(parts[3]) if parts[3].isdigit() else None,
        'gpu_utilization_percent': int(parts[4]) if parts[4].isdigit() else None,
        'pcie_generation_max': int(parts[5]) if parts[5].isdigit() else None,
        'pcie_generation_current': int(parts[6]) if parts[6].isdigit() else None,
        'pcie_link_width_max': int(parts[7]) if parts[7].isdigit() else None,
        'pcie_link_width_current': int(parts[8]) if parts[8].isdigit() else None,
    }


def connect_db():
    return sqlite3.connect(DB_PATH)


def insert_task(args):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    host_name = socket.gethostname()
    gpu = get_gpu_info()
    power_profile = get_power_profile()

    con = connect_db()
    cur = con.cursor()
    cur.execute('''
        INSERT INTO gpu_tasks (
            task_name, task_type, status, start_time, host_name,
            gpu_name, gpu_bus_id, pcie_generation_max, pcie_generation_current,
            pcie_link_width_max, pcie_link_width_current,
            gpu_memory_used_mb, gpu_memory_total_mb, gpu_utilization_percent,
            power_profile, input_path, output_path, model_name,
            error_message, notes, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        args.task_name,
        args.task_type,
        args.status,
        args.start_time or now,
        host_name,
        gpu.get('gpu_name'),
        gpu.get('gpu_bus_id'),
        gpu.get('pcie_generation_max'),
        gpu.get('pcie_generation_current'),
        gpu.get('pcie_link_width_max'),
        gpu.get('pcie_link_width_current'),
        gpu.get('gpu_memory_used_mb'),
        gpu.get('gpu_memory_total_mb'),
        gpu.get('gpu_utilization_percent'),
        power_profile,
        args.input_path,
        args.output_path,
        args.model_name,
        args.error_message,
        args.notes,
        now,
    ))
    task_id = cur.lastrowid
    con.commit()
    con.close()
    return task_id


def update_task(args):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    gpu = get_gpu_info()
    power_profile = get_power_profile()

    con = connect_db()
    cur = con.cursor()
    current = cur.execute('SELECT start_time FROM gpu_tasks WHERE id = ?', (args.id,)).fetchone()
    duration = None
    if current and current[0] and args.end_time:
        try:
            start_dt = datetime.strptime(current[0], '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(args.end_time, '%Y-%m-%d %H:%M:%S')
            duration = round((end_dt - start_dt).total_seconds(), 1)
        except Exception:
            duration = None

    cur.execute('''
        UPDATE gpu_tasks
        SET status = ?,
            end_time = ?,
            duration_seconds = COALESCE(?, duration_seconds),
            gpu_name = COALESCE(?, gpu_name),
            gpu_bus_id = COALESCE(?, gpu_bus_id),
            pcie_generation_max = COALESCE(?, pcie_generation_max),
            pcie_generation_current = COALESCE(?, pcie_generation_current),
            pcie_link_width_max = COALESCE(?, pcie_link_width_max),
            pcie_link_width_current = COALESCE(?, pcie_link_width_current),
            gpu_memory_used_mb = COALESCE(?, gpu_memory_used_mb),
            gpu_memory_total_mb = COALESCE(?, gpu_memory_total_mb),
            gpu_utilization_percent = COALESCE(?, gpu_utilization_percent),
            power_profile = COALESCE(?, power_profile),
            output_path = COALESCE(?, output_path),
            model_name = COALESCE(?, model_name),
            error_message = COALESCE(?, error_message),
            notes = COALESCE(?, notes),
            updated_at = ?
        WHERE id = ?
    ''', (
        args.status,
        args.end_time or now,
        duration,
        gpu.get('gpu_name'),
        gpu.get('gpu_bus_id'),
        gpu.get('pcie_generation_max'),
        gpu.get('pcie_generation_current'),
        gpu.get('pcie_link_width_max'),
        gpu.get('pcie_link_width_current'),
        gpu.get('gpu_memory_used_mb'),
        gpu.get('gpu_memory_total_mb'),
        gpu.get('gpu_utilization_percent'),
        power_profile,
        args.output_path,
        args.model_name,
        args.error_message,
        args.notes,
        now,
        args.id,
    ))
    con.commit()
    con.close()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='command', required=True)

    start = sub.add_parser('start')
    start.add_argument('--task-name', required=True)
    start.add_argument('--task-type')
    start.add_argument('--status', default='running')
    start.add_argument('--start-time')
    start.add_argument('--input-path')
    start.add_argument('--output-path')
    start.add_argument('--model-name')
    start.add_argument('--error-message')
    start.add_argument('--notes')

    end = sub.add_parser('end')
    end.add_argument('--id', type=int, required=True)
    end.add_argument('--status', default='completed')
    end.add_argument('--end-time')
    end.add_argument('--output-path')
    end.add_argument('--model-name')
    end.add_argument('--error-message')
    end.add_argument('--notes')

    args = ap.parse_args()

    if args.command == 'start':
        task_id = insert_task(args)
        print(json.dumps({'id': task_id, 'status': args.status}, ensure_ascii=False))
    elif args.command == 'end':
        update_task(args)
        print(json.dumps({'id': args.id, 'status': args.status}, ensure_ascii=False))


if __name__ == '__main__':
    main()
