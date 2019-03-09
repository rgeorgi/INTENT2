import string
from typing import List, Union, Sized

import xigt
import re

def ref_match(o, target_ref, ref_type):
    if ref_type in o.attributes:
        my_ref = o.attributes.get(ref_type)
        if my_ref and target_ref in xigt.ref.ids(my_ref):
            return True
    return False

def seg_match(seg): return lambda o: ref_match(o, seg, xigt.consts.SEGMENTATION)
def cnt_match(cnt): return lambda o: ref_match(o, cnt, xigt.consts.CONTENT)
def aln_match(aln): return lambda o: ref_match(o, aln, xigt.consts.ALIGNMENT)
def dep_match(dep): return lambda o: ref_match(o, dep, xigt.consts.DS_DEP_ATTRIBUTE)

def type_match(type): return lambda o: o.type == type
def id_match(id): return lambda o: o.id == id
def id_base_match(id_base): return lambda o: get_id_base(o.id) == id_base
def attr_match(attr): return lambda o: set(attr.items()).issubset(set(o.attributes.items()))

def tag_match(tag): return lambda o: tag in o.attributes.get('tag', '').split('+')

def get_id_base(id_str):
    """
    Return the "base" of the id string. This should either be everything leading up to the final numbering, or a hyphen-separated letter.

    :param id_str:
    :type id_str:
    """
    s = re.search('^(\S+?)(?:[0-9]+|-[a-z])?$', id_str).group(1)
    return s

def _find_in_self(obj, filters=list):
    """
    Check to see if this object matches all of the filter functions in filters.

    :param filters: List of functions to apply to this object. All filters have a logical and
                    applied to them.
    :type filters: list
    """

    assert len(filters) > 0, "Must have selected some attribute to filter."

    # Iterate through the filters...
    for filter in filters:
        if not filter(obj): # If one evaluates to false...
            return None      # ..we're done. Exit with "None"

    # If we make it through all the iteration, we're a match. Return.
    return obj



def _build_filterlist(**kwargs):
    filters = []
    for kw, val in kwargs.items():
        if kw == 'id':
            filters += [id_match(val)]
        elif kw == 'content':
            filters += [cnt_match(val)]
        elif kw == 'segmentation':
            filters += [seg_match(val)]
        elif kw == 'id_base':
            filters += [id_base_match(val)]
        elif kw == 'attributes':
            filters += [attr_match(val)]
        elif kw == 'type':
            filters += [type_match(val)]
        elif kw == 'alignment':
            filters += [aln_match(val)]
        elif kw == 'tag':
            filters += [tag_match(val)]

        elif kw == 'others': # Append any other filters...
            filters += val
        else:
            raise ValueError('Invalid keyword argument "%s"' % kw)

    return filters

def xigt_find(obj: Union[xigt.Item, xigt.Tier, xigt.Igt, xigt.XigtCorpus],
              **kwargs) -> Union[xigt.Item, xigt.Tier, None]:
    """
    Way to search a xigt instance recursively using a number of
    filters.
        * id
        * content
        * segmentation
        * id_base
        * attributes
        * type
        * alignment
        * tag
        * others [function evaluate truth on searched items]
    """
    found = _find_in_self(obj, _build_filterlist(**kwargs))
    if found is not None:
        return obj

    # If we are working on a container object, iterate
    # over its children.
    elif isinstance(obj, xigt.mixins.XigtContainerMixin):
        found = None
        for child in obj:
            found = xigt_find(child, **kwargs)
            if found is not None:
                break
        return found

def xigt_findall(obj: Union[xigt.Item, xigt.Tier, xigt.Igt, xigt.XigtCorpus],
                 **kwargs) -> List[Union[xigt.Item, xigt.Tier]]:
    """
    List-returning version of the xigt_find function.
    """
    found = []
    found_item = _find_in_self(obj, _build_filterlist(**kwargs))
    if found_item is not None:
        found = [found_item]

    # If we are working on a container object, iterate over
    # the children.
    if isinstance(obj, xigt.mixins.XigtContainerMixin):
        for child in obj:
            found += xigt_findall(child, **kwargs)


    return found

def unique_id_str(id_base: str, existing_tiers: Sized):
    if not existing_tiers:
        return id_base
    else:
        return id_base + '_{}'.format(string.ascii_letters[len(existing_tiers)])

def generate_tier_id(inst: xigt.Igt, tier_type: str,
                     tier_annotating_1: str, tier_annotating_2: str=None) -> str:
    """
    Given an instance, and some information about the tier type
    and what other tier(s) it is annotating, return a unique id.
    """
    if tier_type == 'bilingual-alignments':
        existing_tiers = xigt_findall(inst, type=tier_type, attributes={'source':tier_annotating_1,
                                                                        'target':tier_annotating_2})
        return unique_id_str('{}_{}_aln'.format(tier_annotating_1, tier_annotating_2), existing_tiers)
    elif tier_type == 'pos':
        existing_tiers = xigt_findall(inst, type=tier_type, alignment=tier_annotating_1)
        return unique_id_str('{}_pos'.format(tier_annotating_1), existing_tiers)
    elif tier_type == 'dependencies':
        existing_tiers = xigt_findall(inst, type=tier_type, attributes={'dep':tier_annotating_1})
        return unique_id_str('{}_ds'.format(tier_annotating_1), existing_tiers)
    else:
        raise Exception('Not implemented')