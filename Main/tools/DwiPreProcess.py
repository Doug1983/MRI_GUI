"""

Pre-processing step for the DWI pipeline. Calls the BrainExtrationTool, EddyCurrent and split from FSL.
Also the ANTs distortion correction antsIntermodalityIntrasubject

Required Inputs: T1w, dwi files
Additional Optional Inputs: T1w gadolinium enhanced, T2w

"""

from nipype.interfaces.fsl import BET, Eddy, ExtractROI
from nipype.interfaces.ants import Registration, N4BiasFieldCorrection, ApplyTransforms

from nipype.interfaces.io import JSONFileSink, DataSink
from nipype import Node, Workflow

from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap

from tools.BaseInterface import *


class DwiPreProcess(BaseInterface):

    def __init__(self, parent, dir_dic, bids):
        super().__init__(parent, dir_dic, bids)

        # Create interfaces ============================================================================================
        # BET
        T1w_BET = Node(BET(), name="T1w_BET")
        T1w_BET.btn_string = 'T1w Brain Extraction'
        self.interfaces.append(T1w_BET)

        T1w_gad_BET = Node(BET(), name="T1w_gad_BET")
        T1w_gad_BET.btn_string = 'T1w Gadolinium Enhanced Brain Extraction'
        self.interfaces.append(T1w_gad_BET)

        T2w_dbs_BET = Node(BET(), name="T2w_dbs_BET")
        T2w_dbs_BET.btn_string = 'T2w DBS Acquisition Brain Extraction'
        self.interfaces.append(T2w_dbs_BET)

        dwi_BET = Node(BET(), name="dwi_BET")
        dwi_BET.btn_string = 'dwi Brain Extraction'
        self.interfaces.append(dwi_BET)

        # BFC
        T1w_BFC = Node(N4BiasFieldCorrection(), name="T1w_BFC")
        T1w_BFC.btn_string = 'T1w Bias Field Correction'
        self.interfaces.append(T1w_BFC)

        # Split
        dwi_ROI_b0 = Node(ExtractROI(), name="dwi_ROI_b0")
        dwi_ROI_b0.btn_string = 'dwi Extract b0'
        self.interfaces.append(dwi_ROI_b0)

        # Eddy current correction
        dwi_Eddy = Node(Eddy(), name="dwi_Eddy")
        dwi_Eddy.btn_string = 'dwi Eddy Current Correction'
        self.interfaces.append(dwi_Eddy)

        # Distortion correction
        # as this section is script/comment heavy it was put into a function
        self.distortion_correction_workflow()

        # Data output (i.e. sink) ======================================================================================
        self.sink = Node(DataSink(), name="sink")
        self.sink.btn_string = 'data sink'
        self.sink.inputs.base_directory = self.dir_dic['data_dir']

        self.jsink = Node(JSONFileSink(), name="jsink")
        self.jsink.btn_string = 'json sink'
        self.jsink.inputs.base_directory = self.dir_dic['data_dir']

        # Initialize workflow ==========================================================================================
        self.wf = Workflow(name='pre_processing')

        # T1w BET to ants N4BiasFieldCorrection
        self.wf.connect([(self.return_interface("T1w_BET"), self.return_interface("T1w_BFC"),
                          [("out_file", "input_image")])])
        self.wf.connect([(self.return_interface("T1w_BET"), self.return_interface("T1w_BFC"),
                          [("mask_file", "mask_image")])])

        # Eddy
        self.wf.connect([(self.return_interface("dwi_BET"), self.return_interface("dwi_Eddy"),
                          [("out_file", "in_file")])])

        self.wf.connect([(self.return_interface("dwi_BET"), self.return_interface("dwi_Eddy"),
                          [("mask_file", "in_mask")])])

        # ROI b0
        self.wf.connect([(self.return_interface("dwi_Eddy"), self.return_interface("dwi_ROI_b0"),
                          [("out_corrected", "in_file")])])

        # Distortion Correction:
        # b0_T1_Reg:
        #   -i: moving image
        #   -r: T1
        #   -x: T1 mask
        self.wf.connect([(self.return_interface("dwi_ROI_b0"), self.return_interface("b0_T1w_Reg"),
                          [("roi_file", "moving_image")])])

        self.wf.connect([(self.return_interface("T1w_BFC"), self.return_interface("b0_T1w_Reg"),
                          [("output_image", "fixed_image")])])

        # test remove as doesn't seem useful (see self.distortion_correction_workflow()) and causes a crash when added
        # self.wf.connect([(self.return_interface("T1w_BET"), self.return_interface("b0_T1w_Reg"),
        #                   [("mask_file", "fixed_image_mask")])])

        # dwi_T1_Tran:
        #   -i: Eddy corrected image
        #   -r: Eddy corrected b0
        #   -t: transforms
        self.wf.connect([(self.return_interface("dwi_Eddy"), self.return_interface("dwi_T1w_Tran"),
                          [("out_corrected", "input_image")])])

        self.wf.connect([(self.return_interface("dwi_ROI_b0"), self.return_interface("dwi_T1w_Tran"),
                          [("roi_file", "reference_image")])])

        self.wf.connect([(self.return_interface("b0_T1w_Reg"), self.return_interface("dwi_T1w_Tran"),
                          [("composite_transform", "transforms")])])

        # BaseInterface generates a dict mapping button strings to the workflow nodes
        # self.map_workflow()
        graph_file = self.wf.write_graph("pre_processing", graph2use='flat')
        self.graph_file = graph_file.replace("pre_processing.png", "pre_processing_detailed.png")

        self.init_settings()
        self.init_ui()

    def init_settings(self):
        # TODO: use a json file to save presets
        # set required input files
        self.required_files['T1w'] = {'data_scans': 'T1w', 'data_sources': 'raw'}
        self.required_files['dwi'] = {'data_scans': 'dwi', 'data_sources': 'raw'}

        # options has to be a list since it can take multiple values
        self.optional_files['T1w Gadolinium'] = {'data_scans': 'T1w', 'options': ['acq-gad'], 'data_sources': 'raw'}
        self.optional_files['T2w DBS'] = {'data_scans': 'T2w', 'options': ['acq-dbs'], 'data_sources': 'raw'}

        # Set default settings for workflow nodes as defined by Vinit Srivastava
        # BET
        self.return_interface('dwi_BET').inputs.frac = 0.2
        self.return_interface('dwi_BET').inputs.functional = True
        self.return_interface('dwi_BET').inputs.mask = True

        self.return_interface('T1w_BET').inputs.frac = 0.3
        self.return_interface('T1w_BET').inputs.mask = True

        self.return_interface('T1w_gad_BET').inputs.frac = 0.45
        self.return_interface('T1w_gad_BET').inputs.mask = True

        self.return_interface('T2w_dbs_BET').inputs.frac = 0.2
        self.return_interface('T2w_dbs_BET').inputs.mask = True

        # BFC
        self.return_interface('T1w_BFC').inputs.dimension = 3

        # Eddy
        self.return_interface('dwi_Eddy').inputs.args = '--ol_nstd=4'

        # dwi_ROI_b0
        self.return_interface('dwi_ROI_b0').inputs.t_min = 0
        self.return_interface('dwi_ROI_b0').inputs.t_size = 1

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

    def distortion_correction_workflow(self):
        # The initial script created by Vinit Srivastava was:
        # antsIntermodalityIntrasubject.sh -d 3 -i eddy_corr_brain_b0.nii.gz -r
        # T1-nonGdE_brain_N4bfc_masked.nii.gz -x T1-nonGdE_brain_mask.nii.gz -w
        # template -o B0toT1SmallWarp -t 2
        #
        # Note: the script antsIntermodalityIntrasubject.sh returns an error regarding a missing template file:
        #  template1Warp.nii.gz does not exist - please specify in order to proceed to steps that map to the template
        # This is expected and means that the second half of the script is not executed nor necessary for this step.
        # https://github.com/ANTsX/ANTs/blob/master/Scripts/antsIntermodalityIntrasubject.sh
        #
        # Additionally, the anatomical T1 brain mask is used in the second part of the script and is not useful in our
        # case.
        #
        # The ants interface from nipype doesn't wrap the antsIntermodalityIntrasubject.sh script
        #
        # antsIntermodalityIntrasubject.sh Script breakdown:
        # Usage: `basename $0`
        #        -d imageDimension
        #        -r anatomicalT1image(brain or whole - head, depending on modality) to align to
        #        -R anatomicalReference image to warp to(often higher resolution thananatomicalT1image)
        #        -i scalarImageToMatch(such as avgerage bold, averge dwi, etc.)
        #        -x anatomicalT1brainmask(should mask out regions that do not appear in scalarImageToMatch)
        #        -t transformType(0 = rigid, 1 = affine, 2 = rigid + small_def, 3 = affine + small_def)
        #        -w prefix of T1 to template transform
        #        -T template space
        #        < OPTARGS >
        #        -o outputPrefix
        #        -l labels in template space
        #        -a auxiliary scalar image/s to warp to template
        #        -b auxiliary dt image to warp to template

        # Initial command runs:
        #       /opt/ants-2.3.1/antsRegistration -d 3 -m MI[anatomicalImage(-r), scalarImage(-i),1,32,Regular,0.25]
        #        -c [1000x500x250x0,1e-7,5] -t Rigid[0.1] -f 8x4x2x1 -s 4x2x1x0
        #        -u 1 -m mattes[anatomicalImage(-r), scalarImage(-i),1,32] -c [50x50x0,1e-7,5] -t SyN[0.1,3,0] -f 4x2x1
        #        -s 2x1x0mm -u 1 -z 1 --winsorize-image-intensities [0.005, 0.995] -o B0toT1Warp
        # -d: dimensionality
        # -m: metric
        #       "MI[fixedImage,movingImage,metricWeight,numberOfBins,<samplingStrategy={None,Regular,Random}>,<samplingPercentage=[0,1]>]" );
        #       "Mattes[fixedImage,movingImage,metricWeight,numberOfBins,<samplingStrategy={None,Regular,Random}>,<samplingPercentage=[0,1]>]" );
        # -c: convergence
        #       "MxNxO"
        #       "[MxNxO,<convergenceThreshold=1e-6>,<convergenceWindowSize=10>]"
        # -t: transform
        #       0:rigid[GradientStep], 1:affine[], 2:composite affine[], 3:similarity[], 4:translation[], 5:BSpline[]
        #       "SyN[gradientStep,<updateFieldVarianceInVoxelSpace=3>,<totalFieldVarianceInVoxelSpace=0>]"
        # -f: shrink-factors
        #       "MxNxO..."
        # -s: smoothing-sigmas
        #       "MxNxO..."
        # -u: use-histogram-matching
        # -z: collapse-output-transforms
        # -o: output transform prefix

        b0_T1w_Reg = Node(Registration(), name="b0_T1w_Reg")
        b0_T1w_Reg.btn_string = 'dwi b0 to T1w Registration'
        # -r, -i, -x will get set via workflow implementation
        # -d
        b0_T1w_Reg.inputs.dimension = 3
        # -m
        b0_T1w_Reg.inputs.metric = ['MI', 'Mattes']
        b0_T1w_Reg.inputs.metric_weight = [1, 1]
        b0_T1w_Reg.inputs.radius_or_number_of_bins = [32, 32]
        b0_T1w_Reg.inputs.sampling_strategy = ['Regular', None]
        b0_T1w_Reg.inputs.sampling_percentage = [0.25, None]
        # -c
        b0_T1w_Reg.inputs.number_of_iterations = [[1000, 500, 250, 0], [50, 50, 0]]
        b0_T1w_Reg.inputs.convergence_threshold = [1e-7,  1e-7]
        b0_T1w_Reg.inputs.convergence_window_size = [5, 5]
        # -t
        b0_T1w_Reg.inputs.transforms = ['Rigid', 'SyN']
        b0_T1w_Reg.inputs.transform_parameters = [(0.1,), (0.1, 3, 0.0)]
        # -f
        b0_T1w_Reg.inputs.shrink_factors = [[8, 4, 2, 1], [4, 2, 1]]
        # -s
        b0_T1w_Reg.inputs.smoothing_sigmas = [[4, 2, 1, 0], [2, 1, 0]]
        b0_T1w_Reg.inputs.sigma_units = ['vox', 'mm']
        # -u
        b0_T1w_Reg.inputs.use_histogram_matching = [True, True]
        # -z
        b0_T1w_Reg.inputs.collapse_output_transforms = True
        # winsorize
        b0_T1w_Reg.inputs.winsorize_lower_quantile = 0.005
        b0_T1w_Reg.inputs.winsorize_upper_quantile = 0.995
        # -o
        b0_T1w_Reg.inputs.output_transform_prefix = 'dwiToT1Warp'

        # Since the antsApplyTransform interface in nipype only accepts the transform list in the reverse order (i.e.
        # the output from the antsRegistration script needs to be flipped) we save the transform files as a single
        # composite file.
        b0_T1w_Reg.inputs.write_composite_transform = True
        self.interfaces.append(b0_T1w_Reg)

        # Althought the antsRegistration interface can output a warped image, we keep the antsApplyTransform node to
        # replicate the original (i.e. not nipype) pipeline and to add the input_image_type parameter.\

        # second script: antsApplyTransforms
        # antsApplyTransforms -d 3 -e 3 -i data.nii.gz -o data_distcorr.nii.gz -r
        # eddy_corr_brain_b0.nii.gz -t B0toT1SmallWarp1Warp.nii.gz -t
        # B0toT1SmallWarp0GenericAffine.mat -v
        dwi_T1w_Tran = Node(ApplyTransforms(), name="dwi_T1w_Tran")
        dwi_T1w_Tran.btn_string = 'dwi to T1w Transformation'
        # -d: dimension
        dwi_T1w_Tran.inputs.dimension = 3
        # -e: input image type
        dwi_T1w_Tran.inputs.input_image_type = 3
        # the -i, -o, -r, -t options are from workflow
        self.interfaces.append(dwi_T1w_Tran)

    # Start processing ===================================================================
    @QtCore.pyqtSlot()
    def go(self):
        # since the conversion takes a while, change cursor to hourglass
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        # Get required and optional files from GUI
        # the comboboxes are generated by script and are always index 1 in each row of HBoxLayouts saved in files_Layout
        file_idx = dict([(x.itemAt(1).widget().name, x.itemAt(1).widget().currentIndex())
                         for x in self.files_layout.children() if type(x) == QHBoxLayout])

        # generate dictionary for output files; input files are in self.curr_files
        # out_files = dict()

        # separate t1w and dwi file
        T1w_file = self.curr_files['file_names'][file_idx['T1w']]
        dwi_file = self.curr_files['file_names'][file_idx['dwi']]
        if file_idx['T1w Gadolinium'] < len(self.curr_files['file_names']):
            T1w_gado = self.curr_files['file_names'][file_idx['T1w Gadolinium']]
            self.return_interface('T1w_gad_BET').inputs.in_file = T1w_gado
        if file_idx['T2w DBS'] < len(self.curr_files['file_names']):
            T2w_dbs = self.curr_files['file_names'][file_idx['T2w DBS']]
            self.return_interface('T2w_dbs_BET').inputs.in_file = T2w_dbs

        # set the bval, bvec, acqp and index files within the dwi directory
        bval = dwi_file.split('.')[0] + '.bval'
        bvec = dwi_file.split('.')[0] + '.bvec'
        acqp = dwi_file.split('.')[0] + '_acqp.txt'
        index = dwi_file.split('.')[0] + '_index.txt'

        # handle file output
        t1_session = self.curr_files['sessions'][file_idx['T1w']]
        if t1_session == 'Empty':
            t1_session = ''
        else:
            t1_session += '.'

        dwi_session = self.curr_files['sessions'][file_idx['dwi']]
        if dwi_session == 'Empty':
            dwi_session = ''
        else:
            dwi_session += '.'

        # Sink
        t1_out = "derivatives." + self.wf.name + "." + self.curr_files['subjects'][file_idx['T1w']] + "." + \
                 t1_session + self.curr_files['data_types'][file_idx['T1w']]

        dwi_out = "derivatives." + self.wf.name + "." + self.curr_files['subjects'][file_idx['dwi']] + "." + \
                  dwi_session + self.curr_files['data_types'][file_idx['dwi']]

        reg_out = "derivatives." + self.wf.name + "." + self.curr_files['subjects'][file_idx['dwi']] + "." + \
                  dwi_session + "transforms"

        # T1w
        self.wf.connect([(self.return_interface('T1w_BET'), self.sink, [("out_file", t1_out + ".@T1w_brain")])])
        self.wf.connect([(self.return_interface('T1w_BET'), self.sink, [("mask_file", t1_out + ".@T1w_mask")])])
        self.wf.connect([(self.return_interface('T1w_BFC'), self.sink, [("output_image", t1_out + ".@T1w_bfc")])])

        # dwi
        self.wf.connect([(self.return_interface('dwi_BET'), self.sink, [("out_file", dwi_out + ".@dwi_brain")])])
        self.wf.connect([(self.return_interface('dwi_BET'), self.sink, [("mask_file", dwi_out + ".@dwi_mask")])])

        # set Eddy out name
        self.return_interface('dwi_Eddy').inputs.out_base = dwi_file.split('.')[0] + '_brain_eddy'
        self.wf.connect([(self.return_interface('dwi_Eddy'), self.sink, [("out_corrected", dwi_out + ".@dwi_eddy")])])
        self.wf.connect([(self.return_interface('dwi_Eddy'), self.sink, [("out_rotated_bvecs", dwi_out +
                                                                          ".@dwi_eddy_bvec")])])
        self.wf.connect([(self.return_interface('dwi_ROI_b0'), self.sink, [("roi_file", dwi_out + ".@dwi_b0")])])

        # Reg and Tran
        self.wf.connect([(self.return_interface('b0_T1w_Reg'), self.sink,
                          [("composite_transform", reg_out + ".@b0_T1_Warp")])])

        self.wf.connect([(self.return_interface('dwi_T1w_Tran'), self.sink,
                          [("output_image", dwi_out + ".@b0_T1_Tran")])])

        # Define substitution strings
        substitutions = [('corrected', 'bfc'),
                         ('roi', 'b0'),
                         ('dwiToT1Warp', self.curr_files['subjects'][file_idx['T1w']] + '_' +
                          t1_session.replace('.', '_') + "from-dwi_to-T1w"),
                         ('brain_eddy_trans', 'brain_eddy_space-T1w'),
                         ('.eddy_rotated_bvecs', '.bvec')]

        # Feed the substitution strings to the DataSink node
        self.sink.inputs.substitutions = substitutions

        # create nipype Node for BET on T1w
        self.return_interface('T1w_BET').inputs.in_file = T1w_file
        self.return_interface('dwi_BET').inputs.in_file = dwi_file

        # Eddy
        self.return_interface('dwi_Eddy').inputs.in_acqp = acqp
        self.return_interface('dwi_Eddy').inputs.in_index = index
        self.return_interface('dwi_Eddy').inputs.in_bvec = bvec
        self.return_interface('dwi_Eddy').inputs.in_bval = bval

        self.wf.run()

        QApplication.restoreOverrideCursor()
        self.parentWidget.post_process_update()
