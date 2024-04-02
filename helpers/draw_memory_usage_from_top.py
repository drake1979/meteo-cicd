from datetime import datetime
from pathlib import Path
from plotly.subplots import make_subplots
import os
import plotly.graph_objects as go
import re
import argparse
import pandas as pd
import numpy as np

def read_file(file_path):
    content = open(file_path)
    return content

def get_files(root_path):
    file_paths = []
    for file in os.listdir(root_path):
        file_path = Path(root_path, file)
        file_paths.append(file_path)
    return file_paths

def parse_files(file_paths, services):
    df_columns = ["Date", "System_memory", "System_swap", "python_uptime", "python_memory_usage", "dotnet_uptime", "dotnet_memory_usage", "Total_memory", "Total_swap"]
    top_usage_values = pd.DataFrame(columns=df_columns)
    for file_path in file_paths:
        row_data = {}
        file_content = read_file(file_path)
        for line in file_content:
            if re.match('^\[.*', line):
                if len(row_data) != 0:
                    top_usage_values = top_usage_values._append(row_data, ignore_index=True)
                    row_data = {}
                time = get_time(line)
                row_data['Date'] = time
            elif re.match('^KiB.Mem.*', line):
                memory_usage, total_memory = get_usage(line, 'Mem :')
                row_data['System_memory'] = memory_usage
                row_data['Total_memory'] = total_memory
            elif re.match('^KiB.Swap.*', line):
                swap_usage, total_swap = get_usage(line, 'Swap:')
                row_data['System_swap'] = swap_usage
                row_data['Total_swap'] = total_swap
            else:
                for service_name in services:
                    match service_name:
                        case "python":
                            memory_usage_column_name = "python_memory_usage"
                            uptime_column_name = "python_uptime"
                        case "dotnet":
                            memory_usage_column_name = "dotnet_memory_usage"
                            uptime_column_name = "dotnet_uptime"
                    if re.match(rf'.*{service_name}$', line):
                        memory_usage, uptime = get_process_usage(line)
                        row_data[memory_usage_column_name] = memory_usage
                        row_data[uptime_column_name] = uptime
    return top_usage_values

def get_usage(line, total_begin):
    line_values = line.split(",")
    total_begin = str(re.escape(total_begin))
    total_end = str(re.escape('total'))
    used_end = str(re.escape('used'))
    total = float(re.findall(total_begin+"(.*)"+total_end, line_values[0])[0]) / 1024 / 1024
    used = float(re.findall("(.*)"+used_end, line_values[2])[0]) / 1024 / 1024
    return used, total

def get_process_usage(line):
    line = re.sub(r'\s+', ' ', line)
    line_values = line.split(' ')
    reserved_memory = line_values[5]
    uptime_value = line_values[10]
    if line_values[0] == '':
        reserved_memory = line_values[6]
        uptime_value = line_values[11]
    used_memory = 0
    if re.match('.*[gG]$', reserved_memory):
        used_memory = float(reserved_memory[:-1])
    elif re.match('.*[mM]$', reserved_memory):
        used_memory = float(reserved_memory[:-1]) / 1024
    elif len(reserved_memory) > 3:
        used_memory = float(reserved_memory) / 1024 / 1024
    else:
        used_memory = float(reserved_memory)
    uptime_value = uptime_value.split('.')[0]
    minutes, seconds = map(int, uptime_value.split(':'))
    uptime = pd.Timedelta(minutes=minutes, seconds=seconds)
    return used_memory, uptime

def calculate_draw_data(parsed_data, services_limits, services):
    for limits in services_limits:
        limits = dict(sorted(limits.items()))
        for limit_num, (date_key, limit_value) in enumerate(limits.items()):
            limit_column_name = limit_value[0] + "_limit"
            limit_value = limit_value[1]
            date_key = datetime.strptime(date_key, '%Y-%m-%d %H:%M')
            if limit_num == 0:
                parsed_data.loc[parsed_data["Date"] < date_key, [limit_column_name]] = limit_value
            if limit_num == len(limits) - 1:
                parsed_data.loc[parsed_data["Date"] >= date_key, [limit_column_name]] = limit_value
            else:
                next_date_key = datetime.strptime(list(limits.keys())[limit_num + 1], '%Y-%m-%d %H:%M')
                parsed_data.loc[(parsed_data["Date"] < next_date_key) & (parsed_data["Date"] >= date_key), [limit_column_name]] = limit_value
    for service in services:
        percentage_column = service + "_memory_percentage"
        usage_column = service + "_memory_usage"
        limit_column_name = service + "_limit"
        parsed_data[percentage_column] = parsed_data[usage_column] / parsed_data[limit_column_name]
        print(parsed_data)
    parsed_data["System_memory_usage"] = parsed_data["System_memory"] / parsed_data["Total_memory"]
    parsed_data["Swap_usage"] = parsed_data["System_swap"] / parsed_data["Total_swap"]
    print(parsed_data['python_limit'])
    print(parsed_data['python_memory_percentage'])
    return parsed_data

def calculate_peaks(usage_data, peak_services, mean_period = 300):
    for service in peak_services:
        memory_usage_column_index = usage_data.columns.get_loc(service + "_memory_usage")
        peak_column = service + "_peaks"
        usage_data[peak_column] = pd.Series(dtype = 'float')
        peak_column_index = usage_data.columns.get_loc(peak_column)
         # draw_data[mean_column_name] = draw_data.loc[:, memory_usage_column].rolling(window=mean_period).mean()
        mean_period_start = int(mean_period / 2)
        mean_period_end = mean_period - mean_period_start
        for row in range(len(usage_data)):
            if row < mean_period_start:
                usage_data.iloc[row, peak_column_index] = None
                continue
            period_data = usage_data.iloc[row - mean_period_start:row + mean_period_end, memory_usage_column_index].to_list()
            top_limit = np.percentile(period_data, 90)
            bottom_limit = np.percentile(period_data, 10)
            if usage_data.iloc[row, memory_usage_column_index] > top_limit:
                usage_data.iloc[row, peak_column_index] = usage_data.iloc[row, memory_usage_column_index]
            if usage_data.iloc[row, memory_usage_column_index] < bottom_limit:
                usage_data.iloc[row, peak_column_index] = usage_data.iloc[row, memory_usage_column_index]
            else:
                usage_data.iloc[row, peak_column_index] = None
    return usage_data

def draw(values, draw_columns):
    fig = make_subplots(
        rows=2, cols=1
    )
    column_index_list = []
    for column_name in draw_columns:
        column_index_list.append(values.columns.get_loc(column_name))
    for index, column_num in enumerate(column_index_list):
        row = 2
        if index < 2:
            row = 1 
        fig.add_trace(
            go.Scatter(
                x=values['Date'].to_list(),
                y=values.iloc[:,column_num].to_list(),
                name=values.columns[column_num]
            ),
            row=row, col=1
        )
    fig.show()

def draw_peaks(values, peak_services):
    fig = make_subplots(
        rows=1, cols=1
    )
    for service in peak_services:
        peak_column = service + "_peaks"
        memory_usage_column = service + "_memory_usage"
        fig.add_trace(
            go.Scatter(
                x=values['Date'].to_list(),
                y=values[peak_column].to_list(),
                mode = 'lines+markers',
                line = dict(
                    width = 2
                )
            ),
            row = 1, col = 1
        )
        fig.add_trace(
            go.Scatter(
                x=values['Date'].to_list(),
                y=values[memory_usage_column].to_list(),
                line = dict(
                    width = 1,
                    dash = 'dash'
                )
            ),
            row = 1, col = 1
        )
    fig.show()
    
def get_time(line):
    time = ''.join(line.split('[')[1].split(']')[0])
    time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    return time

def parse_arg_values():
    root_path = ""
    parser = argparse.ArgumentParser(description='Draw graf for memory usage from top')
    parser.add_argument('--path', type=str, help='Path to log files contains top output')
    parser.add_argument('--mean_perid', type=str, help='Mean moving window period')
    args = parser.parse_args()
    
    if args.path:
        root_path = Path(args.path)
    if args.mean_path:
        mean_period = int(args.mean_path)
    return root_path, mean_period

if __name__ == '__main__':
    run_env = "prod"
    services = ["dotnet", "python"]
    prod_limits = [{
        "2024-03-22 9:42": ["dotnet", 30],
        "2024-03-21 9:09": ["dotnet", 20],
        "2023-11-24 17:51": ["dotnet", 12]
    },
    {
        "2024-03-22 9:41": ["python", 18],
        "2024-03-21 9:08": ["python", 12],
        "2023-11-24 17:50": ["python", 12]
    }]
    uat_limits = [{
        "2024-02-28 16:09": ["dotnet", 20],
        "2023-11-24 17:51": ["dotnet", 12]
    },
    {
        "2024-02-28 16:08": ["python", 12],
        "2023-11-24 17:50": ["python", 12]
    }]
    draw_columns = ["System_memory_usage", "Swap_usage", "python_memory_percentage", "dotnet_memory_percentage"]
    peak_services = ["dotnet"]
    root_path, mean_period = parse_arg_values()
    parsed_data = parse_files(get_files(root_path), services)
    # service_restart_dates = parsed_data[parsed_data['Dotnet_uptime'] < parsed_data['Dotnet_uptime'].shift(1)]
    if run_env == "prod":
        draw_data = calculate_draw_data(parsed_data, prod_limits, services)
    if run_env == "uat":
        draw_data = calculate_draw_data(parsed_data, uat_limits, services)
    draw_data = calculate_peaks(draw_data, peak_services, mean_period)
    print(draw_data)
    draw(draw_data, draw_columns)
    draw_peaks(draw_data, peak_services)
