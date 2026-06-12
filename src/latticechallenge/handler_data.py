#
import zipfile
import bz2
# import json
import shutil
from pathlib import Path

class HandlerData:
    info_challenge_data = {
        "Lattice_Challenge": {
            "Lattice_dimension": "",
            "Reference_dimension": "",
            "Modulus": "",
            "Lattice_basis": ""
        },
        "SVP_Challenge": {
            "Lattice_basis": "",
            "Lattice_dimension": "",
            "Seed": ""
        },
        "Ideal_Lattice_Challenge": {
            "Lattice_basis": "",
            "Lattice_dimension": "",
            "Index_of_a_cyclotomic_polynomial": "",
            "Seed": "",
            "Coefficients_of_the_cyclotomic_polynomial": ""
        },
        "LWE_Challenge": {
            "Secret_dimension": "",
            "Number_of_samples": "",
            "Modulus": "",
            "Relative_error_size": "",
            "Target_vector": "",
            "Lattice_basis": ""
        }
    }

    def __init__(self, workspace: str = None):
        self.workspace = (Path(workspace) if isinstance(workspace, str) else workspace) / "data"
        if not self.workspace.is_dir():
            raise f"Folder {self.workspace} not found ..."
        self.temp = self.workspace / "temp"
        self.folder_owner = None
    
    def export_data_from_txt(self, file: Path):
        if not file.name.endswith(".txt"):
            raise f"Only TXT-file -> {file}"
        with open(file, "r") as f:
            data = f.read()
        result = {}
        count = 0
        variables = []
        variable = 0
        flag_matrix = False
        flag_list = False
        flag_not_empty = False
        for s in data:
            if s.isdigit():
                flag_not_empty = True
                variable = (10 * variable) + int(s)
            else:
                if s == ".":
                    flag_not_empty = False
                    variable = 1.0
                if flag_not_empty:
                    if flag_list:
                        variables.append(variable)
                    else:
                        if flag_matrix:
                            result[count].append(variables)
                        else:
                            result[count] = variable
                            count += 1
                    variable = 0
                    flag_not_empty = False
                if s == "[":
                    if flag_list:
                        flag_matrix = True
                        result[count] = []
                    else:
                        flag_list = True
                elif s == "]":
                    if flag_list:
                        if flag_matrix:
                            result[count].append(variables)
                        else:
                            result[count] = variables
                            count += 1
                        
                        flag_list = False
                        variables = []
                    else:
                        flag_matrix = False
                        count += 1
        return result
    
    def get_files_from_folder(self, folder: Path):
        files = []
        for f in folder.iterdir():
            if f.is_file():
                files.append(f)
            else:
                files += self.get_files_from_folder(f)
        return files
    
    def unzipping(self, file: Path) -> list:
        names = []
        if file.name.endswith(".zip"):
            with zipfile.ZipFile(file, 'r') as z:
                names = z.namelist()
                z.extractall(self.temp)
        elif file.name.endswith(".bz2"):
            file_txt = self.temp / file.name.replace(".bz2", ".txt")
            names = [file_txt.name]
            with bz2.open(file, 'rb') as f_in:
                with open(file_txt, 'wb') as f_out:
                    f_out.write(f_in.read())
        else:
            print("Error... (unzipping)")
        return names
    
    def handler_folder_temp(self, operation: str, namefunc: str):
        if operation == "create":
            if self.folder_owner == None:
                self.temp.mkdir(parents=True, exist_ok=True)
                self.folder_owner = namefunc
        elif operation == "delete":
            if namefunc == self.folder_owner:
                shutil.rmtree(self.temp)
                self.folder_owner = None
        else:
            raise f"Command not found ... {operation}"
    
    def get_namefiles(self, challenge: str = "all"):
        filenames = []
        for chall in (self.info_challenge_data.keys() if challenge == "all" else [challenge]):
            folder = self.workspace / chall
            if not folder.is_dir():
                raise f"Folder {chall} not found ... Directory: {self.workspace}"
            filenames += [f.name for f in self.get_files_from_folder(self.workspace)]
        return sorted(filenames)
    
    def get_info_challenge_from_files(self):
        information = {}
        self.handler_folder_temp("create", "gicffs")
        for file in self.get_files_from_folder(self.workspace):
            information = {**information, **self.get_info_challenge_from_file(file)}
        self.handler_folder_temp("delete", "gicffs")
        return information

    def get_info_challenge_from_file(self, file: Path):
        files = []
        information = {}
        if file.name.endswith(".txt"):
            files = [file]
        else:
            self.handler_folder_temp("create", "gicff")
            for subname in self.unzipping(file):
                subfile = self.temp / subname
                files.append(subfile)
        for f in files:
            information[f.name.replace(".txt", "")] = self.get_info_challenge_from_file_txt(f)
            if not file.name.endswith(".txt"):
                f.unlink()
        self.handler_folder_temp("delete", "gicff")
        return information

    def get_info_challenge_from_file_txt(self, file: Path):
        data = self.export_data_from_txt(file)
        information = {}
        if file.name.startswith("challenge-"):
            information["Lattice_dimension"] = data[0]
            information["Reference_dimension"] = data[1]
            information["Modulus"] = data[2]
            information["Lattice_basis"] = data[3]
        elif file.name.startswith("svpchallengedim"):
            dim_and_seed = file.name[15:-4].split("seed")
            # dim_and_seed = file.name.replace("svpchallengedim", "").replace(".txt", "").split("seed")
            information["Lattice_basis"] = data[0]
            information["Lattice_dimension"] = int(dim_and_seed[0])
            information["Seed"] = int(dim_and_seed[1])
        elif file.name.startswith("ideallatticedim"):
            information["Lattice_basis"] = data[0]
            information["Lattice_dimension"] = data[1]
            information["Index_of_a_cyclotomic_polynomial"] = data[2]
            information["Seed"] = data[3]
            information["Coefficients_of_the_cyclotomic_polynomial"] = data[4]
        elif file.name.startswith("LWE_"):
            res = round((data[3] / (1000 if data[3] > 1000 else 100) - 1), 3)
            information["Secret_dimension"] = data[0]
            information["Number_of_samples"] = data[1]
            information["Modulus"] = data[2]
            information["Relative_error_size"] = res
            information["Target_vector"] = data[4]
            information["Lattice_basis"] = data[5]
        else:
            raise f"Error filename -> {file.name}"
        return information