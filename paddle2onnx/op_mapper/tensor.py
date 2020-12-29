#   Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import numpy as np
from paddle2onnx.constant import dtypes
from paddle2onnx.op_mapper import OpMapper as op_mapper
from paddle2onnx.op_mapper import mapper_helper


@op_mapper('concat')
class Concat():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        node = graph.make_node(
            'Concat',
            inputs=node.input('X'),
            outputs=node.output('Out'),
            axis=node.attr('axis'))


@op_mapper('expand_as_v2')
class ExpandAsV2():
    support_opset_verison_range = (8, 12)

    @classmethod
    def opset_8(cls, graph, node, **kw):
        target_shape = node.attr('target_shape')
        if node.input('target_tensor', 0) is not None:
            target_shape = graph.make_node(
                'Shape', inputs=[node.input('target_tensor', 0)])
        elif target_shape is not None:
            target_shape = graph.make_node(
                'Constant',
                attrs={'dtype': dtypes.ONNX.INT64,
                       'value': target_shape})
        else:
            raise Exception(
                "Not find attribute: 'target_shape' or tensor 'target_tensor'")
        node = graph.make_node(
            'Expand',
            inputs=[node.input('X', 0), target_shape],
            outputs=node.output('Out'))


@op_mapper('expand_v2')
class ExpandV2():
    support_opset_verison_range = (8, 12)

    @classmethod
    def opset_8(cls, graph, node, **kw):
        node = graph.make_node(
            'Expand',
            inputs=[node.input('X', 0), node.input('Shape', 0)],
            outputs=node.output('Out'))


@op_mapper('shape')
class Shape():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        graph.make_node(
            'Shape', inputs=node.input('Input'), outputs=node.output('Out'))


@op_mapper('split')
class Split():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        sections = node.attr('sections')
        if len(sections) > 0:
            graph.make_node(
                'Split',
                inputs=node.input('X'),
                outputs=node.output('Out'),
                axis=node.attr('axis'),
                split=sections)
        else:
            graph.make_node(
                'Split',
                inputs=node.input('X'),
                outputs=node.output('Out'),
                axis=node.attr('axis'))


@op_mapper(['slice', 'strided_slice'])
class Slice():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        axes = node.attr('axes')
        starts = node.attr('starts')
        ends = node.attr('ends')
        steps = node.attr('strides', [1] * len(ends))
        if steps != [1] * len(ends):
            raise Exception(
                "Slice in onnx(opset<10) not support attribute 'step', Try converting with opset_version >=10"
            )
        graph.make_node(
            "Slice",
            inputs=[node.input('Input')[0]],
            outputs=node.output('Out'),
            axes=axes,
            starts=starts,
            ends=ends)

    @classmethod
    def opset_10(cls, graph, node, **kw):
        axes = node.attr('axes')
        starts = node.attr('starts')
        ends = node.attr('ends')
        steps = node.attr('strides', [1] * len(ends))

        axes_node = graph.make_node(
            'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                               'value': axes})
        starts_node = graph.make_node(
            'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                               'value': starts})
        ends_node = graph.make_node(
            'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                               'value': ends})
        steps_node = graph.make_node(
            'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                               'value': steps})
        graph.make_node(
            "Slice",
            inputs=[
                node.input('Input')[0], starts_node, ends_node, axes_node,
                steps_node
            ],
            outputs=node.output('Out'))


@op_mapper(['expand', 'tile'])
class Expand():
    support_opset_verison_range = (11, 12)

    @classmethod
    def opset_11(cls, graph, node, **kw):
        expand_times = node.attr('expand_times')
        if expand_times is None:
            expand_times = node.attr('repeat_times')

        if 'repeat_times_tensor' in node.inputs and len(
                node.input('repeat_times_tensor')) == 1:
            graph.make_node(
                "Tile",
                inputs=[
                    node.input('X', 0), node.input('repeat_times_tensor', 0)
                ],
                outputs=node.output('Out'))
        elif 'RepeatTimes' in node.inputs and len(node.input(
                'RepeatTimes')) == 1:
            graph.make_node(
                "Tile",
                inputs=[node.input('X', 0), node.input('RepeatTimes', 0)],
                outputs=node.output('Out'))
        elif expand_times is None:
            raise Exception("Not find attribute: 'repeat_times'.")
        elif -1 not in expand_times:
            expand_times_node = graph.make_node(
                'Constant',
                attrs={'dtype': dtypes.ONNX.INT64,
                       'value': expand_times})
            graph.make_node(
                "Tile",
                inputs=[node.input('X', 0), expand_times_node],
                outputs=node.output('Out'))
        else:
            raise Exception("illegal Tensor: 'repeat_times'.")


@op_mapper('range')
class Range():
    support_opset_verison_range = (6, 12)

    @classmethod
    def opset_6(cls, graph, node, **kw):
        start = node.input('Start', 0)
        end = node.input('End', 0)
        step = node.input('Step', 0)
        #graph.make_node(
        #    "Range",
        #    inputs=[start, end, step],
        #    outputs=node.output('Out'))
        #return 
        start_t = graph.make_node('Squeeze', inputs=[start], axes=[0])
        end_t = graph.make_node('Squeeze', inputs=[end], axes=[0])
        step_t = graph.make_node('Squeeze', inputs=[step], axes=[0])
        graph.make_node(
            "Range",
            inputs=[start_t, end_t, step_t],
            outputs=node.output('Out'))


@op_mapper('fill_constant')
class Constant():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        value = node.attr('value')
        dtype = node.attr('dtype')
        shape = node.attr('shape')
        value = np.ones(shape) * value
        value = value.astype(dtypes.DTYPE_PADDLE_NUMPY_MAP[dtype])
        value = value.flatten().tolist()
        graph.make_node(
            'Constant',
            inputs=[],
            outputs=node.output('Out'),
            attrs={
                'dims': shape,
                'dtype': dtypes.DTYPE_PADDLE_ONNX_MAP[dtype],
                'value': value
            })


@op_mapper('fill_constant_batch_size_like')
class FillConstantBatchSizeLike():
    support_opset_verison_range = (9, 12)

    @classmethod
    def opset_9(cls, graph, node, **kw):
        input_dim_idx = tensor_shape = graph.make_node(
            'Constant',
            dtype=dtypes.ONNX.INT64,
            dims=[1],
            value=node.attr('input_dim_idx'))
        output_dim_idx = tensor_shape = graph.make_node(
            'Constant',
            dtype=dtypes.ONNX.INT64,
            dims=[1],
            value=node.attr('output_dim_idx'))
        input_shape = graph.make_node('Shape', inputs=node.input('Input'))
        updates = graph.make_node('Gather', inputs=[input_shape, input_dim_idx])
        tensor_shape = tensor_shape = graph.make_node(
            'Constant',
            attrs={'dtype': dtypes.ONNX.INT64,
                   'value': node.attr('shape')})
        tensor_shape = graph.make_node(
            'ScatterND', inputs=[tensor_shape, output_dim_idx, updates])
        dtype = dtypes.DTYPE_PADDLE_ONNX_MAP[node.attr('dtype')]
        graph.make_node(
            'ConstantOfShape',
            inputs=[tensor_shape],
            outputs=node.output('Out'),
            dims=[1],
            dtype=dtype,
            value=node.attr('value'))


@op_mapper('fill_any_like')
class FullLike():
    '''
    fill_any_like is kernel for paddle op::full_like & ones_like
    '''
    support_opset_verison_range = (9, 12)

    @classmethod
    def opset_9(cls, graph, node, **kw):
        shape_node = graph.make_node('Shape', inputs=node.input('X'))
        value = node.attr('value')
        dtype = node.attr('dtype')
        input_dtype = node.input_var('X', 0).dtype
        if dtype is None:
            dtype = input_dtype
        dtype = dtypes.DTYPE_PADDLE_ONNX_MAP[dtype]
        graph.make_node(
            'ConstantOfShape',
            inputs=[shape_node],
            outputs=node.output('Out'),
            dims=[1],
            dtype=dtype,
            value=value)


@op_mapper('gather')
class Gather():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        if len(node.input_shape('Index', 0)) == 1:
            # gather
            graph.make_node(
                'Gather',
                inputs=[node.input('X', 0), node.input('Index', 0)],
                outputs=node.output('Out'))
        else:
            raise Exception(
                "please try to convert OP:gather(indices's rank >1) with opset_version >= 11."
            )

    @classmethod
    def opset_11(cls, graph, node, **kw):
        if len(node.input_shape('Index', 0)) == 1:
            # gather
            graph.make_node(
                'Gather',
                inputs=[node.input('X', 0), node.input('Index', 0)],
                outputs=node.output('Out'))
        else:
            # gather_nd 
            graph.make_node(
                'GatherND',
                inputs=[node.input('X', 0), node.input('Index', 0)],
                outputs=node.output('Out'))


@op_mapper('squeeze2')
class Squeeze():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        axes = node.attr('axes')
        graph.make_node(
            'Squeeze',
            inputs=[node.input('X', 0)],
            outputs=node.output('Out'),
            axes=axes)


@op_mapper('assign_value')
class Assign():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        if len(node.input_names) > 0:
            graph.make_node(
                'Identity', inputs=node.input('X'), outputs=node.output('Out'))
        else:
            parameters = {}
            value = np.array(node.attr('fp32_values'))
            if value is None:
                value = np.array(node.attr('int32_values'))
            parameter = {
                'data': value,
                'dtype': node.attr('dtype'),
                'shape': node.attr('shape')
            }
            parameters[node.output('Out', 0)] = parameter
            graph.build_parameters(parameters)


@op_mapper('transpose2')
class Transpose():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        graph.make_node(
            'Transpose',
            inputs=node.input('X'),
            outputs=node.output('Out'),
            perm=node.attr('axis'))


@op_mapper('flatten2')
class Flatten():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        graph.make_node(
            'Flatten',
            inputs=node.input('X'),
            outputs=node.output('Out'),
            axis=node.attr('axis'))


@op_mapper('flatten_contiguous_range')
class FlattenContiguousRange():
    support_opset_verison_range = (5, 12)

    @classmethod
    def opset_5(cls, graph, node, **kw):
        dims = len(node.input_shape('X', 0))
        start_axis = node.attr('start_axis')
        end_axis = node.attr('stop_axis')
        shape_node = graph.make_node('Shape', inputs=node.input('X'))
        slice1 = mapper_helper.slice_helper(
            graph, shape_node, axes=[0], starts=[0], ends=[start_axis])
        slices = [
            slice1, graph.make_node(
                'Constant', value=[-1], dtype=dtypes.ONNX.INT64)
        ]
        if end_axis < dims - 1:
            slice3 = mapper_helper.slice_helper(
                graph, shape_node, axes=[0], starts=[end_axis + 1],
                ends=[dims])
            slices = [
                slice1, graph.make_node(
                    'Constant', value=[-1], dtype=dtypes.ONNX.INT64), slice3
            ]
        final_shape = graph.make_node('Concat', inputs=slices, axis=0)
        graph.make_node(
            'Reshape',
            inputs=[node.input('X')[0], final_shape],
            outputs=node.output('Out'))


@op_mapper('reshape2')
class Reshape():
    support_opset_verison_range = (5, 12)

    @classmethod
    def opset_5(cls, graph, node, **kw):
        shape_name = 'ShapeTensor'
        if shape_name not in node.inputs or len(node.input(shape_name)) == 0:
            shape_name = 'Shape'
        if shape_name not in node.inputs or len(node.input(shape_name)) == 0:
            if node.attr('shape') is None or len(node.attr('shape')) == 0:
                raise Exception("shape tensor and shape attrubite all unkown.")
        if len(node.input(shape_name)) > 1:
            cast_shape_nodes = []
            for i in range(len(node.input(shape_name))):
                dim = node.input(shape_name)[i]
                cast_node = graph.make_node(
                    'Cast', inputs=[dim], to=dtypes.ONNX.INT64)
                cast_shape_nodes.append(cast_node)
            shape_node = graph.make_node(
                'Concat', inputs=cast_shape_nodes, axis=-1)
            graph.make_node(
                'Reshape',
                inputs=[node.input('X')[0], shape_node],
                outputs=node.output('Out'))
        elif len(node.input(shape_name)) == 1:
            cast_shape_node = graph.make_node(
                'Cast', inputs=node.input(shape_name), to=dtypes.ONNX.INT64)
            graph.make_node(
                'Reshape',
                inputs=[node.input('X')[0], cast_shape_node],
                outputs=node.output('Out'))
        elif node.attr('shape') is not None and len(node.attr('shape')) > 0:
            shape_node = graph.make_node(
                'Constant',
                attrs={
                    'dtype': dtypes.ONNX.INT64,
                    'value': node.attr('shape')
                })
            reshape_node = graph.make_node(
                'Reshape',
                inputs=[node.input('X')[0], shape_node],
                outputs=node.output('Out'))


@op_mapper('unsqueeze2')
class Unsqueeze():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        graph.make_node(
            'Unsqueeze',
            inputs=node.input('X'),
            outputs=node.output('Out'),
            axes=node.attr('axes'))


@op_mapper('reciprocal')
class Reciprocal():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        graph.make_node(
            'Reciprocal', inputs=node.input('X'), outputs=node.output('Out'))


@op_mapper('cast')
class Cast():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        graph.make_node(
            'Cast',
            inputs=node.input('X'),
            outputs=node.output('Out'),
            to=dtypes.DTYPE_PADDLE_ONNX_MAP[node.attr('out_dtype')])


@op_mapper('clip')
class Clip():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        min_value = node.attr('min')
        max_value = node.attr('max')
        if node.input('Max', 0) is None:
            max_ = max_value
        else:
            max_ = node.input('Max', 0)
        if node.input('Min', 0) is None:
            min_ = min_value
        else:
            min_ = node.input('minx', 0)
        mapper_helper.clip_helper(graph,
                                  node.input('X', 0), max_, min_,
                                  node.output('Out', 0))


@op_mapper(['pad2d', 'pad3d'])
class Pad():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        pads = cls.convert_padding(node, **kw)
        value = None
        if node.attr('pad_value') is not None:
            value = node.attr('pad_value')
        elif node.attr('value') is not None:
            value = node.attr('value')
        graph.make_node(
            'Pad',
            inputs=node.input('X'),
            outputs=node.output('Out'),
            mode=node.attr('mode'),
            value=value,
            pads=pads)

    @classmethod
    def opset_11(cls, graph, node, **kw):
        pads = cls.convert_padding(node, **kw)
        pads_node = graph.make_node(
            'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                               'value': pads})
        value = None
        if node.attr('pad_value') is not None:
            value = node.attr('pad_value')
        elif node.attr('value') is not None:
            value = node.attr('value')
        value_node = graph.make_node(
            'Constant', attrs={'dtype': dtypes.ONNX.FLOAT,
                               'value': value})

        graph.make_node(
            'Pad',
            inputs=node.input('X') + [pads_node, value_node],
            outputs=node.output('Out'),
            mode=node.attr('mode'))

    @classmethod
    def convert_padding(cls, node, **kw):
        x_shape = node.input_shape('X', 0)
        paddings = node.attr('paddings')
        onnx_paddings = None
        #TODO support pads is Variable
        if node.attr('data_format') == 'NCHW':
            onnx_paddings = [
                0, 0, paddings[0], paddings[2], 0, 0, paddings[1], paddings[3]
            ]
        elif node.attr('data_format') == 'NHWC':
            onnx_paddings = [
                0, paddings[0], paddings[2], 0, 0, paddings[1], paddings[3], 0
            ]
        elif node.attr('data_format') == 'NCDHW':
            onnx_paddings = [
                0, 0, paddings[4], paddings[2], paddings[0], 0, 0, paddings[5],
                paddings[3], paddings[1]
            ]
        return onnx_paddings


@op_mapper('uniform_random_batch_size_like')
class UniformRandom():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        graph.make_node(
            'RandomUniformLike',
            inputs=node.input('Input'),
            outputs=node.output('Out'),
            high=node.attr('max'),
            dtype=dtypes.DTYPE_PADDLE_ONNX_MAP[node.attr('dtype')],
            low=node.attr('min'),
            seed=float(node.attr('seed')), )


@op_mapper('uniform_random')
class UniformRandom():
    support_opset_verison_range = (1, 12)

    @classmethod
    def opset_1(cls, graph, node, **kw):
        shape = node.output_shape('Out', 0)
        graph.make_node(
            'RandomUniform',
            outputs=node.output('Out'),
            high=node.attr('max'),
            dtype=dtypes.DTYPE_PADDLE_ONNX_MAP[node.attr('dtype')],
            low=node.attr('min'),
            seed=float(node.attr('seed')),
            shape=shape)


@op_mapper(
    [
        'bilinear_interp', 'nearest_interp', 'bilinear_interp_v2',
        'nearest_interp_v2'
    ],
    mapper_dict={
        'bilinear_interp': 'linear',
        'nearest_interp': 'nearest',
        'bilinear_interp_v2': 'linear',
        'nearest_interp_v2': 'nearest'
    })
class Resize():
    support_opset_verison_range = (9, 12)

    @classmethod
    def opset_9(cls, graph, node, **kw):
        inputs = [node.input('X')[0]]
        resize_type = kw['mapper_dict'][node.type]
        if node.attr('align_corners') or node.attr('align_mode') == 0:
            raise Exception(
                "Resize in onnx(opset<=10) only support coordinate_transformation_mode: " \
                "'asymmetric', Try converting with opset_version 11"
            )
        if len(node.input('OutSize')) > 0 or len(node.input('SizeTensor')) > 0:
            in_shape, out_shape = cls.compute_output_shape(
                graph, node, opset_version=9)
            cast_shape_node2 = graph.make_node(
                'Cast', inputs=[out_shape], to=dtypes.ONNX.FLOAT)
            cast_shape_node0 = graph.make_node(
                'Cast', inputs=[in_shape], to=dtypes.ONNX.FLOAT)
            node_h_w_scales = graph.make_node(
                'Div', inputs=[cast_shape_node2, cast_shape_node0])
            inputs.append(node_h_w_scales)
        elif 'Scale' in node.inputs and len(node.input('Scale')) > 0:
            scale = node.input('Scale')[0]
            inputs.append(out_shape)
        else:
            out_shape = [node.attr('out_h'), node.attr('out_w')]
            scale = node.attr('scale')
            if out_shape.count(-1) > 0:
                scale_node = graph.make_node(
                    'Constant',
                    attrs={
                        'dtype': dtypes.ONNX.FLOAT,
                        'value': [1, 1, scale, scale]
                    })
                inputs.append(scale_node)
            else:
                raise Exception("Unexpected situation happend")
        graph.make_node(
            'Upsample',
            inputs=inputs,
            outputs=node.output('Out'),
            mode=resize_type)

    @classmethod
    def opset_10(cls, graph, node, **kw):
        inputs = [node.input('X')[0]]
        resize_type = kw['mapper_dict'][node.type]
        if node.attr('align_corners') or node.attr('align_mode') == 0:
            raise Exception(
                "Resize in onnx(opset<=10) only support coordinate_transformation_mode:" \
                " 'asymmetric', Try converting with opset_version 11"
            )
        if len(node.input('OutSize')) > 0 or len(node.input('SizeTensor')) > 0:
            in_shape, out_shape = cls.compute_output_shape(graph, node)
            cast_shape_node2 = graph.make_node(
                'Cast', inputs=[out_shape], to=dtypes.ONNX.FLOAT)
            cast_shape_node0 = graph.make_node(
                'Cast', inputs=[in_shape], to=dtypes.ONNX.FLOAT)
            node_h_w_scales = graph.make_node(
                'Div', inputs=[cast_shape_node2, cast_shape_node0])
            inputs.append(node_h_w_scales)
        elif 'Scale' in node.inputs and len(node.input('Scale')) > 0:
            scale = node.input('Scale')[0]
            inputs.append(scale)
        else:
            out_shape = [node.attr('out_h'), node.attr('out_w')]
            scale = node.attr('scale')
            if isinstance(scale, float):
                scale = [1, 1, scale, scale]
            else:
                scale = [1, 1] + scale
            if out_shape.count(-1) > 0:
                scale_node = graph.make_node(
                    'Constant',
                    attrs={'dtype': dtypes.ONNX.FLOAT,
                           'value': scale})
                inputs.append(scale_node)
            else:
                raise Exception("Unexpected situation happend")
        graph.make_node(
            'Resize',
            inputs=inputs,
            outputs=node.output('Out'),
            mode=resize_type)

    @classmethod
    def opset_11(cls, graph, node, **kw):
        node_lists = []
        resize_type = kw['mapper_dict'][node.type]
        coordinate_transformation_mode = ''
        if node.attr('align_corners'):
            coordinate_transformation_mode = 'align_corners'
        elif node.type == 'nearest_interp':
            coordinate_transformation_mode = 'half_pixel'
        else:
            if node.attr('align_mode') == 1:
                coordinate_transformation_mode = 'asymmetric'
            else:
                coordinate_transformation_mode = 'half_pixel'
        roi_node = graph.make_node(
            'Constant',
            attrs={
                'dtype': dtypes.ONNX.FLOAT,
                'value': [1, 1, 1, 1, 1, 1, 1, 1]
            })
        inputs = [node.input('X')[0], roi_node]
        node_lists.append(roi_node)
        if len(node.input('OutSize')) > 0 or len(node.input('SizeTensor')) > 0:
            empty_node = graph.make_node(
                'Constant', attrs={'dtype': dtypes.ONNX.FLOAT,
                                   'value': []})
            inputs.append(empty_node)
            _, out_shape = cls.compute_output_shape(graph, node)
            inputs.append(out_shape)
        elif len(node.input('Scale')) > 0:
            scale = node.input('Scale')[0]
            inputs.append(scale)
        else:
            out_shape = [node.attr('out_h'), node.attr('out_w')]
            scale = node.attr('scale')
            if isinstance(scale, float):
                scale = [1, 1, scale, scale]
            else:
                scale = [1, 1] + scale

            if out_shape.count(-1) > 0:
                scale_node = graph.make_node(
                    'Constant',
                    attrs={'dtype': dtypes.ONNX.FLOAT,
                           'value': scale})
                inputs.append(scale_node)
            else:
                empty_node = graph.make_node(
                    'Constant',
                    attrs={'dtype': dtypes.ONNX.FLOAT,
                           'value': []})
                in_shape, out_shape = cls.compute_output_shape_by_size(graph,
                                                                       node)
                inputs += [empty_node, out_shape]
        graph.make_node(
            'Resize',
            inputs=inputs,
            outputs=node.output('Out'),
            mode=resize_type,
            coordinate_transformation_mode=coordinate_transformation_mode)

    @classmethod
    def compute_output_shape(cls, graph, node, opset_version=10):
        shape_node0 = graph.make_node('Shape', inputs=node.input('X'))
        if opset_version < 10:
            shape_node1 = graph.make_node(
                'Slice', inputs=[shape_node0], starts=[0], ends=[2])
        else:
            starts_node = graph.make_node(
                'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                                   'value': [0]})
            ends_node = graph.make_node(
                'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                                   'value': [2]})
            shape_node1 = graph.make_node(
                'Slice', inputs=[shape_node0, starts_node, ends_node])
        if len(node.input('OutSize')) > 0:
            cast_shape_node = graph.make_node(
                'Cast', inputs=node.input('OutSize'), to=dtypes.ONNX.INT64)
        else:
            concat_shape_node = graph.make_node(
                "Concat", inputs=node.input('SizeTensor'), axis=0)
            cast_shape_node = graph.make_node(
                'Cast', inputs=[concat_shape_node], to=dtypes.ONNX.INT64)
        shape_node2 = graph.make_node(
            'Concat', inputs=[shape_node1, cast_shape_node], axis=0)
        return shape_node0, shape_node2

    @classmethod
    def compute_output_shape_by_size(cls, graph, node, opset_version=10):
        shape_node0 = graph.make_node('Shape', inputs=node.input('X'))
        if opset_version < 10:
            shape_node1 = graph.make_node(
                'Slice', inputs=[shape_node0], starts=[0], ends=[2])
        else:
            starts_node = graph.make_node(
                'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                                   'value': [0]})
            ends_node = graph.make_node(
                'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                                   'value': [2]})
            shape_node1 = graph.make_node(
                'Slice', inputs=[shape_node0, starts_node, ends_node])
        out_shape = [node.attr('out_h'), node.attr('out_w')]
        shape_node2 = graph.make_node(
            'Constant', attrs={'dtype': dtypes.ONNX.INT64,
                               'value': out_shape})
        shape_node3 = graph.make_node(
            'Concat', inputs=[shape_node1, shape_node2], axis=0)
        return shape_node0, shape_node3
