import os
import re
import pathlib
import nibabel.nicom.dicomwrappers as dicom_wrap


class Parser:

    def __init__(self):
        self.clear_files()

        # reg ex for dicom files
        # matches are : FILE, NBR and EXTENSION(optional)
        self.dicom_regex = re.compile(r"(?P<File>.*\D)(?P<Nbr>\d{1,4})(?P<Ext>\D*)$|(?P<Default>.*)")

    def clear_files(self):
        # variables definition
        # each bids sub-folder will be held in an array
        self.file_names = []  # full path of current file
        self.formats = []  # .nii.gz, dicom, .json

        self.data_types = []  # anat, ct, dwi
        self.data_sources = []  # raw, sourcedata, derivatives
        self.data_scans = []  # scan type: t1, t2, ct, dwi
        self.options = []  # tuple containing: desc, acq, space

        self.subjects = []  # sub-XX
        self.sessions = []  # ses-XX

    def walk_path(self, base_dir):
        self.clear_files()
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
                if file_ext.lower() in ['.dcm', ''] and file_name.upper() in ['DICOMDIR'] or \
                        file_name[0:3].upper() in ['KEY']:
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

        regex = re.compile(r"(?P<Source>sourcedata|derivatives|templates)|(?P<Sub>sub-[a-zA-Z0-9]+)|" +
                           "(?P<Sess>ses-[a-zA-Z0-9]+)|" +
                           "(?P<options>(acq|space|desc)-[a-zA-Z0-9]+)|(?P<Anat>[tT][1-9][w]?)|(?P<dwi>[dD][wW][iI])|" +
                           "(?P<ct>[cC][tT])")

        for i, file in enumerate(self.file_names):
            curr_source = 'Empty'
            curr_sess = 'Empty'
            curr_sub = 'Empty'
            curr_type = 'Empty'
            curr_scan = 'Empty'
            curr_options = []

            match = list(regex.finditer(file))
            for mat in match:
                if mat.group('Source') is not None:
                    if mat.group('Source') in ['templates']:
                        curr_source = mat.group('Source')
                    elif mat.group('Source') in ['derivatives', 'sourcedata'] and curr_source != 'templates':
                        curr_source = mat.group('Source')
                elif mat.group('Source') is None and curr_source == 'Empty':
                    curr_source = 'raw'

                if mat.group('Sub') is not None:
                    curr_sub = mat.group('Sub')

                if mat.group('Sess') is not None:
                    curr_sess = mat.group('Sess')

                if mat.group('Anat') is not None:
                    if mat.group('Anat')[-1] != 'w':
                        curr_scan = mat.group('Anat') + 'w'
                    else:
                        curr_scan = mat.group('Anat')
                    curr_type = 'anat'

                if mat.group('dwi') is not None:
                    curr_type = 'dwi'
                    curr_scan = mat.group('dwi')

                if mat.group('ct') is not None:
                    curr_type = 'ct'
                    curr_scan = mat.group('ct')

                if mat.group('options') is not None:
                    curr_options.append(mat.group('options'))

            # append data
            self.data_types.append(curr_type)
            self.data_sources.append(curr_source)
            self.data_scans.append(curr_scan)
            self.options.append(curr_options)

            self.subjects.append(curr_sub)
            self.sessions.append(curr_sess)

    def return_files(self, file_filters):

        # filters is a dictionary containing filter values
        id_set = set(range(0, len(self.file_names)))

        id_set = self.apply_filter(id_set, self.options, 'options', file_filters)
        id_set = self.apply_filter(id_set, self.data_types, 'data_types', file_filters)
        id_set = self.apply_filter(id_set, self.data_sources, 'data_sources', file_filters)
        id_set = self.apply_filter(id_set, self.data_scans, 'data_scans', file_filters)
        id_set = self.apply_filter(id_set, self.formats, 'formats', file_filters)
        id_set = self.apply_filter(id_set, self.sessions, 'sessions', file_filters)
        id_set = self.apply_filter(id_set, self.subjects, 'subjects', file_filters)
        id_set = self.apply_filter(id_set, self.file_names, 'file_names', file_filters)

        return_dict = dict()
        return_dict['options'] = [self.options[i] for i in id_set]
        return_dict['data_types'] = [self.data_types[i] for i in id_set]
        return_dict['data_sources'] = [self.data_sources[i] for i in id_set]
        return_dict['data_scans'] = [self.data_scans[i] for i in id_set]
        return_dict['file_names'] = [self.file_names[i] for i in id_set]
        return_dict['formats'] = [self.formats[i] for i in id_set]
        return_dict['subjects'] = [self.subjects[i] for i in id_set]
        return_dict['sessions'] = [self.sessions[i] for i in id_set]

        return return_dict

    def return_subjects(self):
        return sorted(set(self.subjects))

    @staticmethod
    def apply_filter(id_set, data, filter_type, file_filters):
        if filter_type in file_filters and filter_type != 'options':
            id_set = id_set.intersection(
                set([i for i in range(len(data)) if data[i] in file_filters[filter_type] and data[i] != '']))
        elif filter_type in file_filters and filter_type == 'options':  # options is a list
            id_set = id_set.intersection(
                set([i for i in range(len(data)) if any([y in file_filters[filter_type] for y in data[i]]) and data[i] != []]))
        else:
            id_set = id_set.intersection(set(range(0, len(data))))
        return id_set
