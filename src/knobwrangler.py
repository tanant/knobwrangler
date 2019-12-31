"""A collection of functions to wrangle nuke knobs

Important: behaviour here is generally verified against Nuke 11!
"""

import re
import nuke


def Group_KnobSet(name, label="", knobs_to_group=None, start_closed=False):
    """Helper function for the weird open/close group system

    This matches the same naming convention you'll find in nuke like
    nuke.Tab_Knob or nuke.Int_Knob etc

    Returns a start/end pair with any supplied knobs between them.

    example usage:
        a = nuke.Int_Knob('more_int', 'more_int knob',100)
        b = nuke.Int_Knob('hello','world', 300)
        grouped_knobs = knobwrangler.Group_KnobSet('hello',
                                      'some things that are neat', [a, b])
        knobwrangler.add_knobs(grouped_knobs, the_node)
    """
    knobs_to_group = [] if knobs_to_group is None else knobs_to_group

    group_start = nuke.Tab_Knob(
        name,
        label,
        nuke.TABBEGINCLOSEDGROUP if start_closed else nuke.TABBEGINGROUP
        )

    group_end = nuke.Tab_Knob(name+'_end', '', nuke.TABENDGROUP)

    return [group_start] + knobs_to_group + [group_end]


def _calculate_insertion_point(existing_knob_list,
                               knob_point=None, insert_before=False):
    """Encapsulates logic on working out where to insert in a the knob list

    Returns an integer index which tells us where to insert.
    For example in list [A,B,C]:
     - before A is 0
     - after A or before B is 1
     - after B or before C is 2
     - after C is 3

    it's basically list.index(item) + 1 if not insert_before, but there is
    extra logic to deal with the case in nuke where you MUST have a tab knob

    Note that this function assumes that the caller will ensure that the tab
    knob situation is correct!
    """

    # simple/default cases. Quick bail
    if knob_point is None:
        # done like this to catch the case of when knob_point is passed in as
        # None as opposed to explicitly defining both true/false paths
        if not insert_before:
            insert_point = len(existing_knob_list)
        else:
            insert_point = 0
    else:
        # if knob_point supplied is not in the user_list? - fail because we
        # can't do what was requested
        if knob_point not in existing_knob_list:
            raise IndexError(
                    "Insert Point - knob '{x}' not in user editable knobs"
                    .format(
                        x=knob_point.name()
                        )
                    )
        else:
            insert_point = existing_knob_list.index(knob_point)

        if not insert_before:
            insert_point += 1

    return insert_point


def _is_a_tab(knob):
    """Helper function to check if a knob is a tab.

    This is _not_ perfect, we use a lazy check to see if the flag to save
    is set. Tab knobs (and group end variants) have the DO_NOT_WRITE flag
    set to be True.
    """
    return isinstance(knob, nuke.Tab_Knob) and knob.getFlag(nuke.DO_NOT_WRITE)


def _user_knob_by_name(the_node, knobname):
    """Specialised function to get stable behaviour for user knobs

    Regular nuke behaviour allows you to add multiple knobs of the same name
    via API which will be resolved at *some* point in the lifecycle (generally
    on copy/paste or save/load)

    Of course, if you do this at in-memory time and ask for a knob back by
    name, it's undefined *which* knob you get back so I've defined the
    behaviour as the FIRST knob with that name.

    Mimics the behaviour of the knob.name() call where you get None back in
    the case of a bad name.
    """
    for knob in all_user_knobs(the_node):
        if knob.name() == knobname:
            return knob

    return None


def _name_mangler(target_name, pool_of_names):
    """suffixes _X to names (regardless of required or not)"""

    # has to start with the target, have an underscore and end with one or
    # more digits. Filters out 'hello_1_1' for the target of 'hello'
    re_pattern = re.compile("^{target}_([0-9]+)$".format(target=target_name))
    candidates = [x for x in pool_of_names if re_pattern.search(x)]
    indexes = [int(re_pattern.search(x).group(1)) for x in candidates]
    indexes.sort()

    # we will always start with index 1, so the range offset is needed here
    # zipping them together means we can match what we want to what is used
    for wanted, used in zip(range(1, len(indexes)+1), indexes):
        if wanted == used:
            continue
        else:
            break
    else:
        wanted = len(indexes)+1
    return "{target}_{index}".format(target=target_name, index=wanted)


def add_knobs(new_knobs, the_node):
    """Helper function that mimics the addKnob function, but in bulk

    Note that this will coerce new_knobs into a list for ease of use. See
    the `insert` function for full details
    """

    if not isinstance(new_knobs, list):
        new_knobs = [new_knobs]
    return insert(new_knobs, the_node)


def all_user_knobs(the_node):
    """Get a list of knobs that the user can theoretically have added

    The way nodes are built, user knobs are knobs after the last non-user one
    and for most _normal_ knobs, it's the `useLifetime` knob.. but there are a
    few special cases this will handle:
     - NoOp, Dot: hide_input
     - StickyNote: bookmark
     - Group: window
    """

    lastknob_class_map = {'Group': 'window',
                          'StickyNote': 'bookmark',
                          'NoOp': 'hide_input',
                          'Dot': 'hide_input',
                          }

    knobs = the_node.allKnobs()
    last_knob_name = lastknob_class_map.get(the_node.Class(), 'useLifetime')
    last_knob = the_node.knob(last_knob_name)
    last_knob_index = knobs.index(last_knob)
    return knobs[last_knob_index+1:]


def pop_user_knobs(the_node):
    """Remove all user knobs and gives them back to you

    Provides them back in the order they originally were so you can keep or
    throw them as desired.
    """

    knobs_to_pop = all_user_knobs(the_node)
    for knob in knobs_to_pop[::-1]:
        the_node.removeKnob(knob)

    return knobs_to_pop


def mangle_knob_name(knob, the_node, rename=False):
    """For the desired knobname give back a mangled version of the name.

    Uses a basic nuke-compatible approach of suffixing _X where X is an
    integer that's counted up from 1.

    You *can* programatically add in multiple copies of a knob that are
    different instances but with the same knobname. When the knob is
    copy/pasted or the script saved and reopened, the naming conflict
    is resolved however in your in-memory session, I don't think there
    is any guarantee which knob you'll get if referencing by name.

    Always returns the correctly mangled name and MAY rename.
    """
    # ah, if this knob is on the node, then we are going to mangle it,
    if knob in the_node.allKnobs():
        return knob.name()

    if knob.name() not in [x.name() for x in the_node.allKnobs()]:
        return knob.name()

    # early bail! This function is safe to use just like this
    new_name = _name_mangler(knob.name(), the_node.knobs().keys())
    if rename:
        knob.setName(new_name)

    return new_name


def insert(new_knobs, the_node, knob_point=None, insert_before=False):
    """Insert the knob(s) specified at the point specified.

    new knobs is an iterable that provides knobs OR a knob

    in english: insert (these knobs) onto (the_node) at the (knob_point),
                and by the way do it (before)

    if insert_before, the knobs will finish before
    if not insert_before, new knobs will start with the knob point

    Special case, if knob_point is None, this means "I don't care" so
    we interpret it as either the very front, or the very back depending
    on the insert_before.

    For ease of use, knob_point can be name or it can be a knob - it will
    be cast the same way in the end.

    Returns the knobs created so you can chain this to some other function
    and this will include the automatic tab creation nuke does
    """
    # we need an iterable to inject into the list
    if not isinstance(new_knobs, list):
        new_knobs = [new_knobs]

    # this is a hard sanity check here, we do NOT protect you from this case
    if len(set(new_knobs)) != len(new_knobs):
        raise ValueError("Duplicate knobs to add, please deduplicate them!")

    if knob_point is not None:
        # convert str - knob reference
        if isinstance(knob_point, str):
            knob_point_name = knob_point
            # use of internal function for stability
            knob_point = _user_knob_by_name(the_node, knob_point_name)

            # if you're here and knob_point is None you supplied a junk path
            if knob_point is None:
                raise ValueError(
                    "Insertion point specified is not a userknob on this node"
                    )
        else:
            knob_point_name = knob_point.name()
            knob_point = knob_point

    pre_change_knobs = all_user_knobs(the_node)

    insert_point = _calculate_insertion_point(
        pre_change_knobs,
        knob_point,
        insert_before
        )

    # copy the original state as we need to capture the delta
    proposed_list = list(pre_change_knobs)

    # so for the annoying case where someone creates a dozen knobs named 'foo'
    # we have to constantly recheck the names pool. *sigh*
    exhausted_names = {x for x in the_node.knobs().keys()}
    for knob in new_knobs:
        if knob.name() not in exhausted_names:
            exhausted_names.add(knob.name())
        else:
            new_name = _name_mangler(knob.name(), exhausted_names)
            knob.setName(new_name)
            exhausted_names.add(new_name)

    proposed_list[insert_point:insert_point] = new_knobs

    # TODO: there is a craaaazy edge case here where the User autotab is
    #       not created at this point and may affect name mangling.

    # finally, we walk through from the front until we hit a difference on
    # the lists. This is where we need to pop back to on the current knobs,
    # and then readd from the new proposed list.
    index = 0
    for index, knob in enumerate(pre_change_knobs):
        if knob != proposed_list[index]:
            break

    for knob in pre_change_knobs[index:]:
        the_node.removeKnob(knob)

    for knob in proposed_list[index:]:
        # TODO: might be nice to log this out
        the_node.addKnob(knob)

    return [x
            for x
            in all_user_knobs(the_node)
            if x not in set(pre_change_knobs)]
