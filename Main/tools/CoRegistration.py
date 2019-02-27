"""

Co-Registration between modalities within subject, such as T1w-CT, T1w-MNI template,...
Note that dwi-T1w is already done as the distortion correction step in pre-processing

Co-registration T1w -> MNI template
ANTs default Unimodal script

Required Inputs: T1w, ct, template files
Additional Optional Inputs:

The template used is the one recommended by Lead-DBS:

MNI152 NLIN 2009b nonlinear asymmetric
http://www.bic.mni.mcgill.ca/~vfonov/icbm/2009/mni_icbm152_nlin_asym_09b_nifti.zip

"""

from nipype.interfaces.fsl import BET  # BET on MNI template
from nipype.interfaces.ants import Registration, ApplyTransforms

from nipype.interfaces.io import JSONFileSink, DataSink
from nipype import Node, Workflow

from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap

from tools.BaseInterface import *


class CoRegistration(BaseInterface):

    def __init__(self, parent, dir_dic, bids):
        super().__init__(parent, dir_dic, bids)

        # Create interfaces ============================================================================================
        # BET
        MNI_BET = Node(BET(), name="MNI_BET")
        MNI_BET.btn_string = 'MNI Template Brain Extraction'
        self.interfaces.append(MNI_BET)

        # Registration
        postopCT_T1_Reg = Node(Registration(), name="postopCT_T1_Reg")
        postopCT_T1_Reg.btn_string = 'post-op CT to T1w Registration'
        self.interfaces.append(postopCT_T1_Reg)

        preopCT_T1_Reg = Node(Registration(), name="preopCT_T1_Reg")
        preopCT_T1_Reg.btn_string = 'pre-op CT to T1w Registration'
        self.interfaces.append(preopCT_T1_Reg)

        T1_MNI_Reg = Node(Registration(), name="T1_MNI_Reg")
        T1_MNI_Reg.btn_string = 'T1w to MNI template Registration'
        self.interfaces.append(T1_MNI_Reg)

        # Transformations
        postopCT_T1_Tran = Node(ApplyTransforms(), name="postopCT_T1_Tran")
        postopCT_T1_Tran.btn_string = 'post-op CT to T1w Transformation'
        self.interfaces.append(postopCT_T1_Tran)

        preopCT_T1_Tran = Node(ApplyTransforms(), name="preopCT_T1_Tran")
        preopCT_T1_Tran.btn_string = 'pre-op CT to T1w Transformation'
        self.interfaces.append(preopCT_T1_Tran)

        T1_MNI_Tran = Node(ApplyTransforms(), name="T1_MNI_Tran")
        T1_MNI_Tran.btn_string = 'T1w to MNI template Transformation'
        self.interfaces.append(T1_MNI_Tran)

        # Data output (i.e. sink) ======================================================================================
        self.sink = Node(DataSink(), name="sink")
        self.sink.btn_string = 'data sink'
        self.sink.inputs.base_directory = self.dir_dic['data_dir']

        self.jsink = Node(JSONFileSink(), name="jsink")
        self.jsink.btn_string = 'json sink'
        self.jsink.inputs.base_directory = self.dir_dic['data_dir']

        # Initialize workflow ==========================================================================================
        self.wf = Workflow(name='co_registration')

        # Brain extracted MNI template to antsRegistration
        # MI[mni_t1_brain.nii.gz,t1_nonGdE_brain_N4bfc_masked.nii.gz,1,32,Regular,0.25]
        # MI[fixedImage,movingImage,metricWeight,numberOfBins,<samplingStrategy={None,Regular,Random}>,<samplingPercentage=[0,1]>]
        self.wf.connect([(self.return_interface("MNI_BET"), self.return_interface("T1_MNI_Reg"),
                          [("out_file", "fixed_image")])])

        self.wf.connect([(self.return_interface("MNI_BET"), self.return_interface("T1_MNI_Tran"),
                          [("out_file", "reference_image")])])

        # T1 -> MNI Reg to Tran
        self.wf.connect([(self.return_interface("T1_MNI_Reg"), self.return_interface("T1_MNI_Tran"),
                          [("composite_transform", "transforms")])])

        # postop CT -> T1 Reg to Tran
        self.wf.connect([(self.return_interface("postopCT_T1_Reg"), self.return_interface("postopCT_T1_Tran"),
                          [("composite_transform", "transforms")])])

        # preop CT -> T1 Reg to Tran
        self.wf.connect([(self.return_interface("preopCT_T1_Reg"), self.return_interface("preopCT_T1_Tran"),
                          [("composite_transform", "transforms")])])

        # BaseInterface generates a dict mapping button strings to the workflow nodes
        self.wf.base_dir = self.dir_dic['temp_dir']

        graph_file = self.wf.write_graph("co_registration", graph2use='flat')
        self.graph_file = graph_file.replace("co_registration.png", "co_registration_detailed.png")

        self.init_settings()
        self.init_ui()

    def init_settings(self):
        # TODO: use a json file to save presets
        # set required input files
        self.required_files['BFC T1w'] = \
            {'data_scans': 'T1w', 'data_sources': 'derivatives', 'file_names': '*_bfc*'}

        self.required_files['MNI Template'] = {'data_scans': 'T1w', 'data_sources': 'templates'}
        self.required_files['Post-Op CT'] = {'data_scans': 'ct', 'sessions': 'ses-postop', 'data_sources': 'raw'}

        # options has to be a list since it can take multiple values
        self.optional_files['Pre-Op CT'] = {'data_scans': 'ct', 'sessions': 'ses-preop', 'data_sources': 'raw'}

        # Set default settings for workflow nodes as defined by Vinit Srivastava
        # BET
        self.return_interface('MNI_BET').inputs.frac = 0.5
        self.return_interface('MNI_BET').inputs.mask = True

        # postopCT_T1_Reg
        self.set_inter_modality_intra_subject_inputs(self.return_interface('postopCT_T1_Reg'), 'fromCT_toT1w')

        # preopCT_T1_Reg
        self.set_inter_modality_intra_subject_inputs(self.return_interface('preopCT_T1_Reg'), 'fromCT_toT1w')

        # T1_MNI_Reg
        self.set_t1_mni_inputs(self.return_interface('T1_MNI_Reg'), 'fromT1_toMNI')

        # postopCT_T1_Tran
        self.set_transform_inputs(self.return_interface('postopCT_T1_Tran'), 'T1w')

        # preopCT_T1_Tran
        self.set_transform_inputs(self.return_interface('preopCT_T1_Tran'), 'T1w')

        # T1_MNI_Tran
        self.set_transform_inputs(self.return_interface('T1_MNI_Tran'), 'MNI')

    def init_ui(self):
        self.layout = QVBoxLayout(self)  # Top: files and settings, bottom: graph

        h_box = QHBoxLayout()
        # Files layout
        self.files_layout = self.generate_files_ui(self.required_files, self.optional_files)
        h_box.addLayout(self.files_layout)
        h_box.addStretch()

        btn_layout = QVBoxLayout()
        btn_layout.addWidget(QLabel('Parameters: '))
        for node in self.interfaces:
            button = QPushButton(str(node.btn_string))
            button.clicked.connect(lambda: self.ui_set_params())
            btn_layout.addWidget(button)
        btn_layout.addStretch()

        h_box.addLayout(btn_layout)
        h_box.addStretch()
        # self.layout.addLayout(btn_layout, 1)

        self.layout.addLayout(h_box)

        self.btn_go = QPushButton('Process Data')
        self.btn_go.clicked.connect(self.go)
        self.btn_go.setFixedWidth(600)
        self.layout.addWidget(self.btn_go)
        self.layout.addStretch()

        # workflow visualization
        wf_layout = QVBoxLayout()
        wf_label = QLabel()
        wf_label.resize(300, 600)
        pixmap = QPixmap(self.graph_file)
        wf_label.setPixmap(pixmap.scaled(pixmap.width()*.5, pixmap.height()*.5, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation))
        wf_layout.addWidget(wf_label)
        wf_layout.addStretch()
        self.layout.addLayout(wf_layout, 4)

    @staticmethod
    def set_inter_modality_intra_subject_inputs(in_node, from_to):
        # see DwiPreProcess.py for information about this script
        # runs :
        # antsRegistration -d 3 -m MI[fixedimg, movingimg, 1, 32, Regular, 0.25] -c[1000x500x250x0, 1e-7, 5] -t
        # Rigid[0.1] -f 8x4x2x1 -s 4x2x1x0 -u 1 -z 1 --winsorize-image-intensities[0.005, 0.995] -o potpotpot

        # -r, -i, -x will get set via workflow implementation
        # -d
        in_node.inputs.dimension = 3
        # -m
        in_node.inputs.metric = ['MI']
        in_node.inputs.metric_weight = [1]
        in_node.inputs.radius_or_number_of_bins = [32]
        in_node.inputs.sampling_strategy = ['Regular']
        in_node.inputs.sampling_percentage = [0.25]
        # -c
        in_node.inputs.number_of_iterations = [[1000, 500, 250, 0]]
        in_node.inputs.convergence_threshold = [1e-7]
        in_node.inputs.convergence_window_size = [5]
        # -t
        in_node.inputs.transforms = ['Rigid']
        in_node.inputs.transform_parameters = [(0.1,)]
        # -f
        in_node.inputs.shrink_factors = [[8, 4, 2, 1]]
        # -s
        in_node.inputs.smoothing_sigmas = [[4, 2, 1, 0]]
        in_node.inputs.sigma_units = ['vox']
        # -u
        in_node.inputs.use_histogram_matching = [True]
        # -z
        in_node.inputs.collapse_output_transforms = True
        # winsorize
        in_node.inputs.winsorize_lower_quantile = 0.005
        in_node.inputs.winsorize_upper_quantile = 0.995
        # -o
        in_node.inputs.output_transform_prefix = from_to
        in_node.inputs.write_composite_transform = True

    @staticmethod
    def set_t1_mni_inputs(in_node, from_to):
        # see DwiPreProcess.py for information about this script
        # Runs:
        # antsRegistration --verbose 1 --dimensionality 3 --float 1 --collapse-output-transforms 1 --output
        # [t1nonGdE_to_mni+step1a_ANTsSyN,t1nonGdE_to_mni+step1a_ANTsSyNWarped.nii.gz,t1no
        # nGdE_to_mni+step1a_ANTsSyNInverseWarped.nii.gz] --interpolation Linear
        # --use-histogram-matching 1 --winsorize-image-intensities [0.005,0.995]
        # --initial-moving-transform [mni_t1_brain.nii.gz,t1_nonGdE_brain_N4bfc_masked.nii.gz,1]
        # --transform Rigid[0.1] --metric
        # MI[mni_t1_brain.nii.gz,t1_nonGdE_brain_N4bfc_masked.nii.gz,1,32,Regular,0.25]
        # --convergence [1000x500x250x100,1e-6,10] --shrink-factors 8x4x2x1 --smoothing-sigmas
        # 3x2x1x0vox --transform Affine[0.1] --metric
        # MI[mni_t1_brain.nii.gz,t1_nonGdE_brain_N4bfc_masked.nii.gz,1,32,Regular,0.25]
        # --convergence [1000x500x250x100,1e-6,10] --shrink-factors 8x4x2x1 --smoothing-sigmas
        # 3x2x1x0vox --transform SyN[0.1,3,0] --metric
        # CC[mni_t1_brain.nii.gz,t1_nonGdE_brain_N4bfc_masked.nii.gz,1,4] --convergence
        # [100x70x50x20,1e-6,10] --shrink-factors 8x4x2x1 --smoothing-sigmas 3x2x1x0vox
        #
        #

        # -r, -i, -x will get set via workflow implementation
        in_node.inputs.dimension = 3
        in_node.inputs.float = True
        in_node.inputs.collapse_output_transforms = True
        in_node.inputs.interpolation = 'Linear'
        in_node.inputs.use_histogram_matching = True
        in_node.inputs.winsorize_lower_quantile = 0.005
        in_node.inputs.winsorize_upper_quantile = 0.995
        in_node.inputs.initial_moving_transform_com = 1

        # Transforms
        in_node.inputs.transforms = ['Rigid', 'Affine', 'SyN']
        in_node.inputs.transform_parameters = [(0.1,), (0.1,), (0.1, 3, 0)]
        in_node.inputs.metric = ['MI', 'MI', 'CC']
        in_node.inputs.metric_weight = [1., 1., 1.]
        in_node.inputs.radius_or_number_of_bins = [32, 32, 4]
        in_node.inputs.smoothing_sigmas = [[3, 2, 1, 0], [3, 2, 1, 0], [3, 2, 1, 0]]
        in_node.inputs.sigma_units = ['vox', 'vox', 'vox']
        in_node.inputs.sampling_strategy = ['Regular', 'Regular', None]
        in_node.inputs.sampling_percentage = [0.25, 0.25, None]
        in_node.inputs.number_of_iterations = [[1000, 500, 250, 100], [1000, 500, 250, 100], [100, 70, 50, 20]]
        in_node.inputs.convergence_threshold = [1e-6, 1e-6, 1e-6]
        in_node.inputs.convergence_window_size = [10, 10, 10]
        in_node.inputs.shrink_factors = [[8, 4, 2, 1], [8, 4, 2, 1], [8, 4, 2, 1]]

        # -o
        in_node.inputs.output_transform_prefix = from_to
        in_node.inputs.output_warped_image = True
        in_node.inputs.output_inverse_warped_image = True
        in_node.inputs.write_composite_transform = True

    @staticmethod
    def set_transform_inputs(in_node, from_to):
        in_node.inputs.dimension = 3
        in_node.inputs.out_postfix = '_space-' + from_to

# Start processing ===================================================================
    @QtCore.pyqtSlot()
    def go(self):
        # since the conversion takes a while, change cursor to hourglass
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        # Get required and optional files from GUI
        # the combo box are generated by script and are always index 1 in each row of HBoxLayouts saved in files_Layout
        file_idx = dict([(x.itemAt(1).widget().name, x.itemAt(1).widget().currentIndex())
                         for x in self.files_layout.children() if type(x) == QHBoxLayout])

        # Required files
        t1w_file = self.curr_files['file_names'][file_idx['BFC T1w']]
        template_file = self.template_files['file_names'][file_idx['MNI Template']]
        ct_file = self.curr_files['file_names'][file_idx['Post-Op CT']]

        # Inputs ====================================================================
        self.return_interface('MNI_BET').inputs.in_file = template_file

        # Reg
        self.return_interface('postopCT_T1_Reg').inputs.moving_image = ct_file
        self.return_interface('postopCT_T1_Reg').inputs.fixed_image = t1w_file

        self.return_interface('T1_MNI_Reg').inputs.moving_image = t1w_file

        # Tran
        self.return_interface('postopCT_T1_Tran').inputs.input_image = ct_file
        self.return_interface('postopCT_T1_Tran').inputs.reference_image = t1w_file

        self.return_interface('T1_MNI_Tran').inputs.input_image = t1w_file

        # handle file output ==========================================================================
        t1_session = self.curr_files['sessions'][file_idx['BFC T1w']]
        if t1_session == 'Empty':
            t1_session = ''
        else:
            t1_session += '.'

        ct_session = self.curr_files['sessions'][file_idx['Post-Op CT']]
        if ct_session == 'Empty':
            ct_session = ''
        else:
            ct_session += '.'

        # Sink
        t1_out = "derivatives." + self.wf.name + "." + self.curr_files['subjects'][file_idx['BFC T1w']] + "." + \
                 t1_session + self.curr_files['data_types'][file_idx['BFC T1w']]

        ct_out = "derivatives." + self.wf.name + "." + self.curr_files['subjects'][file_idx['Post-Op CT']] + "." + \
                 ct_session + self.curr_files['data_types'][file_idx['Post-Op CT']]

        reg_out = "derivatives." + self.wf.name + "." + self.curr_files['subjects'][file_idx['Post-Op CT']] + "." + \
                  t1_session + "transforms"

        template_out = "derivatives." + self.wf.name + ".templates"

        # MNI BET
        self.wf.connect([(self.return_interface('MNI_BET'), self.sink, [("out_file", template_out + ".@MNI_brain")])])
        self.wf.connect([(self.return_interface('MNI_BET'), self.sink, [("mask_file", template_out + ".@MNI_mask")])])

        # CT to T1w Reg
        self.wf.connect([(self.return_interface('postopCT_T1_Reg'), self.sink,
                          [("composite_transform", reg_out + ".@ct")])])
        self.wf.connect([(self.return_interface('postopCT_T1_Reg'), self.sink,
                          [("inverse_composite_transform", reg_out + ".@ct_rev")])])

        # T1w MNI Reg
        self.wf.connect([(self.return_interface('T1_MNI_Reg'), self.sink,
                          [("composite_transform", reg_out + ".@T1_MNI_Tran")])])
        self.wf.connect([(self.return_interface('T1_MNI_Reg'), self.sink,
                          [("inverse_composite_transform", reg_out + ".@T1_MNI_Rev_Tran")])])
        self.wf.connect([(self.return_interface('T1_MNI_Reg'), self.sink,
                          [("warped_image", reg_out + ".@T1_MNI_Warped")])])

        # Tran
        self.wf.connect([(self.return_interface('postopCT_T1_Tran'), self.sink,
                          [("output_image", ct_out + ".@ct_Tran")])])

        self.wf.connect([(self.return_interface('T1_MNI_Tran'), self.sink,
                          [("output_image", t1_out + ".@T1_MNI_Tran")])])

        # Define substitution strings
        substitutions = [('corrected', 'bfc')]

        # Feed the substitution strings to the DataSink node
        self.sink.inputs.substitutions = substitutions

        # Optional files
        if file_idx['Pre-Op CT'] < len(self.curr_files['file_names']):
            preop_ct_file = self.curr_files['file_names'][file_idx['Pre-Op CT']]
            self.return_interface('preopCT_T1_Reg').inputs.fixed_image = t1w_file
            self.return_interface('preopCT_T1_Reg').inputs.moving_image = preop_ct_file
            self.return_interface('preopCT_T1_Tran').inputs.input_image = preop_ct_file
            self.return_interface('preopCT_T1_Tran').inputs.input_image = t1w_file

            self.wf.connect([(self.return_interface('preopCT_T1_Reg'), self.sink,
                              [("composite_transform", reg_out + ".@preopct")])])
            self.wf.connect([(self.return_interface('preopCT_T1_Reg'), self.sink,
                              [("inverse_composite_transform", reg_out + ".@preopct_rev")])])
            self.wf.connect([(self.return_interface('preopCT_T1_Tran'), self.sink,
                              [("output_image", ct_out + ".@preopct_Tran")])])
        else:
            self.wf.remove_nodes((self.return_interface('preopCT_T1_Reg'), self.return_interface('preopCT_T1_Tran')))

        # Run
        self.wf.run()

        QApplication.restoreOverrideCursor()
        self.parentWidget.post_process_update()
