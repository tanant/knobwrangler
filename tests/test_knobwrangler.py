import unittest
import logging
import traceback

import nuke
import knobwrangler

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.WARN)

# kick into DEBUG for gory details
# kick into INFO for more messages that may help debugging


class TestKnobwrangler(unittest.TestCase):
    # there should be no variation in any of these.. but yeah. just to be sure
    # this covers 2D, 3D, Deep, the weird NoOp/Dot types, and the StickyNote
    # ...not that I'm encouraging smart StickyNotes btw :P
    NODE_CLASSES_TO_CYCLE = ('Grade',
                             'Axis',
                             'DeepMerge',
                             'Group',
                             'NoOp',
                             'Dot',
                             'StickyNote',
                             )

    def setUp(self):
        self.nodes = {}
        for node_class in self.NODE_CLASSES_TO_CYCLE:
            self.nodes[node_class] = nuke.createNode(node_class, inpanel=False)
            self.nodes[node_class].setSelected(False)
            _LOGGER.debug("created {node_class}:{name}".format(
                    node_class=node_class,
                    name=self.nodes[node_class].name()
                    )
                )

    def tearDown(self):
        for node_class in self.nodes:
            self.nodes[node_class] = None
        nuke.scriptClear()

    @classmethod
    def _int_knob(cls, knobname="generic_int_knob"):
        return nuke.Int_Knob(knobname, "int knob")

    @classmethod
    def _tab_knob(cls):
        return nuke.Tab_Knob("my_user_tab", "UnitTest Testing")

    def test_name_mangling(self):
        for node_class, the_node in self.nodes.items():
            _LOGGER.info("test node class {x}".format(x=node_class))
            new_knob = self._int_knob('hello')
            knobs_added = knobwrangler.add_knobs(new_knob, the_node)
            self.assertTrue(
                knobs_added[-1].name() == 'hello',
                msg="knob name mangled without needing"
                )

            new_knob = self._int_knob('label')
            knobs_added = knobwrangler.add_knobs(new_knob, the_node)
            self.assertTrue(
                knobs_added[-1].name() != 'label',
                msg="knob name NOT mangled even though it's a duplicate"
                )

    def test_simple_knob_addition(self):
        for node_class, node in self.nodes.items():
            _LOGGER.info("test node class {x}".format(x=node_class))
            new_knob = self._int_knob()
            knobs_added = knobwrangler.add_knobs(new_knob, node)
            self.assertIsNot(
                node.knob(new_knob.name()),
                None,
                msg="knob was not added"
                )

            self.assertTrue(
                len(knobs_added) == 2,
                msg="Only one knob added, likely no auto tab!"
                )

            self.assertTrue(
                knobs_added[-1] == node.allKnobs()[-1],
                msg="knob added is not last in list"
                )

    def test_no_name_duplication(self):
        """Does the module protect you from duplicate names?"""
        for node_class, node in self.nodes.items():
            _LOGGER.info("test node class {x}".format(x=node_class))
            tab_knob = self._tab_knob()
            new_knob = self._int_knob()
            another_knob = self._int_knob()
            knobs_added = knobwrangler.add_knobs(
                [tab_knob, new_knob, another_knob],
                node
                )
            self.assertNotEqual(
                knobs_added[1].name(),
                knobs_added[2].name(),
                msg="duplicate knobnames added"
                )

    def test_invalid_insertion_point(self):
        """No insertion points other than ones fully under user control

        There is ONE case, but it'd have to be the last default knob - that's
        not worth coding around.
        """

        for node_class, the_node in self.nodes.items():
            _LOGGER.info("test node class {x}".format(x=node_class))
            with self.assertRaises(ValueError):
                # setup should creat clean nodes
                knobwrangler.insert(self._int_knob("Z"),
                                    the_node,
                                    knob_point="THISCANTBEHERE")

                # all knobs should have a label
                knobwrangler.insert(self._int_knob("Z"),
                                    the_node,
                                    knob_point="label")

    def test_before_after_insertion(self):
        for node_class, node in self.nodes.items():
            _LOGGER.info("test node class {x}".format(x=node_class))

            Tab_Knob = self._tab_knob()
            E_knob = self._int_knob("E")
            G_knob = self._int_knob("G")
            setup_knobs_for_add = [Tab_Knob,
                                   self._int_knob("A"),
                                   self._int_knob("C"),
                                   E_knob,
                                   G_knob,
                                   ]

            knobwrangler.add_knobs(setup_knobs_for_add, node)

            # we are using two different insert methods, by name and by knob
            knobwrangler.insert(self._int_knob('B-after-A'),
                                node,
                                knob_point='A'
                                )

            knobwrangler.insert(self._int_knob('B-before-C'),
                                node,
                                knob_point='C',
                                insert_before=True
                                )

            knobwrangler.insert(self._int_knob('F-after-E'),
                                node,
                                knob_point=E_knob,
                                insert_before=False)

            knobwrangler.insert(self._int_knob('F-before-G'),
                                node,
                                knob_point=G_knob,
                                insert_before=True
                                )

            user_knob_names = [
                x.name()
                for x
                in knobwrangler.all_user_knobs(node)
                ]

            correct_knob_name_order = [Tab_Knob.name(),
                                       'A',
                                       'B-after-A',
                                       'B-before-C',
                                       'C',
                                       'E',
                                       'F-after-E',
                                       'F-before-G',
                                       'G',
                                       ]
            self.longMessage = False
            self.assertEqual(
                len(user_knob_names),
                len(correct_knob_name_order)
                )

            self.longMessage = True
            self.assertEqual(
                user_knob_names,
                correct_knob_name_order,
                msg='Insertion order is incorrect'
                )


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestKnobwrangler, 'test'))
    return suite
