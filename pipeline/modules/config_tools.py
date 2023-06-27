import os, json, sys, re, shutil
import pandas as pd
import numpy as np
import platform

from constants import *

def validate_config(config):
    if "application" not in config.keys():
        print(f"ERROR: Application name not provided in config")
        return False
    if "application_category" not in config.keys():
        print(f"ERROR: Application Category name not provided in config")
        return False

    return True
    

def create_application_config(src_config: dict):
    pipeline_home_path = os.getenv(PIPELINE_HOME_VAR)

    application_home = os.path.join(pipeline_home_path, APPLICATION_FOLDER_NAME)
    if not os.path.isdir(application_home):
        os.mkdir(application_home)
    
    application_path = os.path.join(application_home, src_config["application"])
    os.mkdir(application_path)

    train_path = os.path.join(application_path, TRAIN_DATASET_FOLDER_NAME)
    os.mkdir(train_path)

    #models path
    models_path = os.path.join(application_path, MODELS_FOLDER_NAME)
    os.mkdir(models_path)

    config = default_config
    config["application"] = src_config["application"] 
    config["application_category"] = src_config["application_category"]
    config["train_folder"] = train_path
    config["dataset"] = str(os.path.join(application_path, TRAIN_DATASET_FOLDER_NAME, DATASET_FILE_NAME))
    config["dataset_pca"] = str(os.path.join(application_path, TRAIN_DATASET_FOLDER_NAME, DATASET_PCA_FILE_NAME))
    config["model_commons_filename"] = str(os.path.join(application_path, MODEL_COMMONS_FILE_NAME))
    config["project_account"] = src_config["project_account"] 
    
    config_path = os.path.join(application_path, APPLICATION_CONFIG_FILE_NAME)
    with open(config_path, "w") as file:
        json.dump(config, file)

def save_application_config(config):
    application = config["application"]

    pipeline_home_path = os.getenv(PIPELINE_HOME_VAR)
    application_path = os.path.join(pipeline_home_path, APPLICATION_FOLDER_NAME, application)
    config_path = os.path.join(application_path, APPLICATION_CONFIG_FILE_NAME)

    with open(config_path, "w") as file:
        json.dump(config, file)

    

def get_application_config(application: str):
    # GET APPLICATION FOLDER FROM ENV
    pipeline_home_path = os.getenv(PIPELINE_HOME_VAR)
    print("***********", pipeline_home_path, APPLICATION_FOLDER_NAME, application)
    application_path = os.path.join(pipeline_home_path, APPLICATION_FOLDER_NAME, application)
    if not os.path.isdir(application_path): #directory doesnt exist
        print(f"Application config was not found, creating a config for `{application}`...")
        create_application_config(application)
    
    config_path = os.path.join(application_path, APPLICATION_CONFIG_FILE_NAME)
    with open(config_path, "r") as file:
        config = json.load(file)
        
    return config
    
    
def create_application_structure(config: dict):
    # GET APPLICATION FOLDER FROM ENV
    pipeline_home_path = os.getenv(PIPELINE_HOME_VAR)
    
    # Create the folder Structure 
    application_name = config["application"]
    application_category = config["application_category"]
    application_run_folder = config["cheetah_app_directory"]
    # Copy all files from run folder to train folder
    
    application_path = os.path.join(pipeline_home_path, APPLICATION_FOLDER_NAME, application_name)
    if not os.path.isdir(application_path): #directory doesnt exist
        print(f"Application config was not found, creating a config for `{application_name}`...")
        create_application_config(config)
    
    pipeline_config_path = os.path.join(application_path, APPLICATION_CONFIG_FILE_NAME)
    pipeline_config = None
    with open(pipeline_config_path, "r") as file:
        pipeline_config = json.load(file)
    
    dest_train = pipeline_config["train_folder"]
    files = os.listdir(application_run_folder)
    filenames=[]
    for filename in files:
        if re.match(r'^'+application_name+'_[0-9_]+\.csv$', filename) :
            shutil.copy2(application_run_folder+"/"+filename, dest_train+"/"+filename)
            filenames.append(filename)
    
    print("I AM MERGING ALL FILES", filenames)
    
    frames = []
    for file in filenames:
        df_test = pd.read_csv(dest_train+'/'+file)
        frames.append(df_test)
        
    result = pd.concat(frames, ignore_index=True)
    uniq_id=[i for i in range(1, result.shape[0]+1, 1)]
    result['uniq_id']=np.array(uniq_id)
    result.to_csv(dest_train+'/'+DATASET_FILE_NAME, header=True, index=False)

    # Create a pipeline configure to train and save models
    config_path = os.path.join(application_path, APPLICATION_CONFIG_FILE_NAME)
    pipeline_config = None
    with open(config_path, "r") as file:
        pipeline_config = json.load(file)
        
    return pipeline_config
    
    
    
    
def check_pre_generate(config: dict, filename: str):
    exit_code = 0
    platform_name = platform.node()
    
    
      
    rel_path = (config['cheetah_app_directory'])
    
    # Check target application folder exists before checking for folders and re-writing file
    isExist = os.path.exists(rel_path)
    
    campaign_folders = []
    campaign_files=[]
    if isExist:
        
        for i in config['runs']:
            campaign_folders.append(i['paths']['cheetah_campaign_name'])
            i['paths']['cheetah_campaign_file']=os.path.join(rel_path, i['paths']['cheetah_campaign_file'])
            campaign_files.append(i['paths']['cheetah_campaign_file'])
            
        print_error = "The folldowing folders: [FOLDER_LIST], already exist. \nPlease delete them or change respective 'cheetah_campaign_name' names before executing 'generate phase' of HARP"
        exist_folder=[]
        for folder in campaign_folders:
            isCExist = os.path.exists(os.path.join(rel_path, folder))
            # print(os.path.join(rel_path,folder), ":", isCExist)
            if isCExist:
                exist_folder.append(folder)
        if len(exist_folder) > 0:
            FOLDER_LIST = ", ".join(exist_folder)
            print_error = print_error.replace("FOLDER_LIST", FOLDER_LIST)
            print(print_error)
            exit_code = 1
    else:
        print("Check 'cheetah_app_directory' in configuration file and ensure the absoulte path to target application is specified")
        exit_code = 1
     
    
    if exit_code == 0:   
        machines = ['local', 'owens', 'owens_gpu', 'pitzer', 'pitzer_gpu', 'pitzer48', 'pitzer48_gpu', 'ascend', 'ascend_gpu']
        
        if config['cheetah_campaign_machine'] not in machines:
            print("Provide a valid 'cheetah_campaign_machine' in configuration file. The acceptable machine should be from list [", ", ".join(machines), "]")
            exit_code = 1
        else:
            spcification = config['cheetah_campaign_machine']
            if spcification == "local":
                do_nothing=0
            elif spcification in ['owens', 'owens_gpu'] and 'owens' not in platform_name:
                print("The 'cheetah_campaign_machine'in configuration file '"+spcification+"' does not match with login node:", platform_name)
                print("Either change the 'cheetah_campaign_machine', or login to the mahine to match specifications")
                exit_code = 1
            elif spcification in ['pitzer', 'pitzer_gpu', 'pitzer48', 'pitzer48_gpu'] and 'pitzer' not in platform_name:
                print("The 'cheetah_campaign_machine' in configuration file '"+spcification+"' does not match with login node:", platform_name)
                print("Either change the 'cheetah_campaign_machine', or login to the mahine to match specifications")
                exit_code = 1
            elif spcification in ['ascend', 'ascend_gpu'] and 'ascend' not in platform_name:
                print("The 'cheetah_campaign_machine' in configuration file '"+spcification+"' does not match with login node:", platform_name)
                print("Either change the 'cheetah_campaign_machine', or login to the mahine to match specifications")
                exit_code = 1
            
    
    
    if exit_code == 0:
        json_object = json.dumps(config, indent=4)
        with open(filename, "w") as outfile:
            outfile.write(json_object)
            
            
        supported_machines= "['local', 'owens', 'owens_gpu', 'pitzer', 'pitzer_gpu', 'pitzer48', 'pitzer48_gpu', 'ascend', 'ascend_gpu']"
        
        so = "{'owens': {'project':'<OSC-Project-Account>'}, 'owens_gpu': {'project':'<OSC-Project-Account>'}, 'pitzer': {'project':'<OSC-Project-Account>'}, 'pitzer_gpu': {'project':'<OSC-Project-Account>'}, 'pitzer48': {'project':'<OSC-Project-Account>'}, 'pitzer48_gpu': {'project':'<OSC-Project-Account>'}, 'ascend': {'project':'<OSC-Project-Account>'}, 'ascend_gpu': {'project':'<OSC-Project-Account>'}}"
        scheduler_options = so.replace('<OSC-Project-Account>', config["project_account"])
        
        # write project name now
        for file in campaign_files:
            filedata=""
            with open(file, 'r') as filer :
                filedata = filer.readlines()
          
            for idx, line in enumerate(filedata):
                if "supported_machines" in line:
                    line = re.sub(r'supported\_machines\s*=\s*.*', "supported_machines = "+ supported_machines, line)
                    filedata[idx]=line
                if "scheduler_options" in line:
                    line = re.sub(r'scheduler\_options\s*=\s*.*', "scheduler_options = "+ scheduler_options, line)
                    filedata[idx]=line
            
            with open(file, 'w') as filew :
                filew.writelines(filedata)

        
    
    print("EXIT CODE:", exit_code, " ")
    return exit_code


default_config = {
    "application": None,
    "application_category": None,
    "dataset": None,
    "dataset_pca": None,
    "train_folder": None,
    "model_commons_filename": None,
    "project_account": None
}
