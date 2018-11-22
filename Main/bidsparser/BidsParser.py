import os
import re
import pathlib
import nibabel.nicom.dicomwrappers as dicom_wrap

class BidsParser(object):

    def __init__(self):
        # variables definition
        # each bids sub-folder will be held in an array
        self.data_types = ['func', 'dwi', 'anat', 'meg', 'ct']
        self.data_sources = ['raw', 'derivatives', 'source']

        self.file_names = []
        self.formats = []

        self.subjects = []
        self.sessions = []

        # reg ex for dicom files
        # matches are : FILE, NBR and EXTENSION(optional)
        self.dicom_regex = re.compile(r"(?P<File>.*\D)(?P<Nbr>\d{1,4})(?P<Ext>\D*)$|(?P<Default>.*)")

    def walk_path(self, base_dir):

        # walk through all sub-folders
        for root, dirs, files in os.walk(base_dir):

            if len(files) > 1:

                # pool multi-file images
                all_files = [self.dicom_regex.match(i).group('File') for i in files]

                all_extensions = [self.dicom_regex.match(i).group('Ext') for i in files]
                duplicates = set([x for x in all_files if all_files.count(x) > 1])

                if len(duplicates) > 0:
                    for dup in duplicates:
                        if dup is not None:
                            same = list(map(lambda x: (x.startswith(dup)), files))
                            ext = set([x for (x, v) in zip(all_extensions, same) if v])

                            # validate that all files have same extension
                            if len(ext) == 1:
                                str_nbr = ([(self.dicom_regex.match(i).group('Nbr')) for (i, v) in zip(files, same) if v])
                                i_nbr = [int(x) for x in str_nbr]

                                # remove matching file-names from the files list
                                files = [i for (i, v) in zip(files, same) if not v]
                                all_extensions = [i for (i, v) in zip(all_extensions, same) if not v]
                                files.append(dup + str_nbr[i_nbr.index(min(i_nbr))] + list(ext)[0])
                                # files.append(dup + '[' + str_nbr[i_nbr.index(min(i_nbr))] + '-' + str_nbr[
                                #    i_nbr.index(max(i_nbr))] + ']' + list(ext)[0])

            for file in files:
                # get file extension
                file_ext = ''.join(pathlib.Path(file).suffixes)
                file_name = file.replace(file_ext, '')

                files_to_append = []
                formats_to_append = []

                # no file extension, but DICOMDIR
                if file_ext.lower() in ['.dcm', ''] and file_name.upper() in ['DICOMDIR']:
                    '''
                    wrapper = dicom_wrap.wrapper_from_file(os.path.join(root, file))
        
                    temp_dicom = dict()
                    for temp in wrapper.dcm_data.DirectoryRecordSequence._list:
                        if temp.DirectoryRecordType == 'IMAGE':
                            match = dicom_regex.match(os.path.join(root, *temp.ReferencedFileID))
        
                            if match.group('File') not in temp_dicom and match.group('File') is not None:
                                temp_dicom[match.group('File')] = [int(match.group('Nbr')), match.group('Ext')]
                            elif match.group('File') in temp_dicom and int(match.group('Nbr')) > \
                                    temp_dicom[match.group('File')][0]:
                                temp_dicom[match.group('File')] = [int(match.group('Nbr')), match.group('Ext')]
        
                    files_to_append = []
                    formats_to_append = []
                    for keys, values in temp_dicom.items():
                        files_to_append.append(keys+'[1-'+str(values[0])+']'+values[1])
                        formats_to_append.append('dicom')
                    '''
                # DICOM file
                elif file_ext.lower() in ['.dcm', '']:

                    # validate dicom format
                    invalid = False
                    try:
                        dicom_wrap.wrapper_from_file(os.path.join(root, file))
                    except:
                        invalid = True

                    if not invalid:
                        files_to_append = [os.path.join(root, file)]
                        formats_to_append = ['dicom']

                # nifti or compressed nifti
                elif file_ext.lower() in ['.nii', '.nii.gz']:
                    files_to_append = [os.path.join(root, file)]
                    formats_to_append = ['nifti']

                elif file_ext.lower() in ['.json']:
                    files_to_append = [os.path.join(root, file)]
                    formats_to_append = ['json']

                # append data to structure
                for i, to_append in enumerate(files_to_append):
                    if to_append not in self.file_names:
                        self.file_names.append(to_append)
                        self.formats.append(formats_to_append[i])
        self.parse_files()

    def parse_files(self):
        regex = re.compile(r"(?P<Source>sourcedata|derivatives)|(?P<Sub>sub-\d+)|(?P<Anat>anat|t1|t2)|(?P<dwi>dwi)|(?P<ct>ct)")

        for file in self.file_names:
            match = list(regex.finditer(file))
            for mat in match:
                if mat.group('Source') is not None:
                    print(mat.group('Source'))
                if mat.group('Sub') is not None:
                    print(mat.group('Sub'))
                if mat.group('Anat') is not None:
                    print(mat.group('Anat'))
                if mat.group('dwi') is not None:
                    print(mat.group('dwi'))
                if mat.group('ct') is not None:
                    print(mat.group('ct'))


if __name__ == '__main__':
    obj = BidsParser()
    obj.walk_path('D:\Sachs_Lab\MRI_GUI\data')
