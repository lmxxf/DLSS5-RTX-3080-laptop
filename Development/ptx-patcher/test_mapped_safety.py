import unittest
from dlssnr_patcher import FP8_DOWN_PATTERN, FP8_PACK_PATTERN
from ptx_mapped import safe_sources, mapped_at

BASE = '''
mov.b32 %r10, 0;
mov.b32 %r11, 0;
cvt.rn.satfinite.e4m3x2.f16x2 %rs1, %r10;
cvt.rn.satfinite.e4m3x2.f16x2 %rs2, %r11;
mov.b32 %r20, {%rs1, %rs2};
'''

def scan(text):
    return safe_sources(text, FP8_DOWN_PATTERN, FP8_PACK_PATTERN)

class MappedSafety(unittest.TestCase):
    def test_local_single_definition(self):
        src = scan(BASE)
        self.assertIn('%r20', mapped_at(src, len(BASE)-1))

    def test_multiline_vector_load_alternate_definition(self):
        src = scan('ld.weak.global.ca.v4.u32 {\n %r20,%r21,%r22,%r23},[%rd10];\n' + BASE)
        self.assertEqual(src.rejected['%r20'], 'pack_multidef')
        self.assertEqual(len(src.defs['%r20']), 2)

    def test_lowercase_label_does_not_swallow_next_instruction(self):
        src = scan('entry_label:\n' + BASE)
        self.assertIn('%r20', src)
        self.assertEqual(len(src.defs['%r10']), 1)

    def test_cta_qualified_vector_load_is_a_definition(self):
        src = scan('ld.shared::cta.v4.u32 {%r20,%r21,%r22,%r23},[%r70];\n' + BASE)
        self.assertEqual(src.rejected['%r20'], 'pack_multidef')
        self.assertEqual(len(src.defs['%r20']), 2)

    def test_cache_qualified_source_write_is_not_ignored(self):
        src = scan('ld.global.L1::no_allocate.b32 %r10,[%rd1];\n' + BASE)
        self.assertEqual(src.rejected['%r20'], 'source_multidef')
        self.assertEqual(len(src.defs['%r10']), 2)

    def test_inline_vector_destination(self):
        src = scan('{mov.b32 %r99, 0; ld.global.v2.u32 {%r10,%r11},[%rd1];}\n' + BASE)
        self.assertEqual(src.rejected['%r20'], 'source_multidef')

    def test_down_in_other_basic_block(self):
        src = scan(BASE.replace('mov.b32 %r20', '$L_join:\nmov.b32 %r20'))
        self.assertEqual(src.rejected['%r20'], 'cross_block_down')

    def test_use_in_other_basic_block(self):
        text = BASE + '$L_next:\nadd.u32 %r40, %r41, 1;'
        src = scan(text)
        self.assertIn('%r20', src)
        self.assertNotIn('%r20', mapped_at(src, len(text)-1))

    def test_predicated_source(self):
        src = scan(BASE.replace('mov.b32 %r10', '@%p1 mov.b32 %r10'))
        self.assertEqual(src.rejected['%r20'], 'source_not_local')

class MultidefControl(unittest.TestCase):
    def test_single_definition_cross_block_forwarding(self):
        text = BASE.replace('mov.b32 %r20', '$L_join:\nmov.b32 %r20') + '$L_use:\nadd.u32 %r40, %r41, 1;'
        src = safe_sources(text, FP8_DOWN_PATTERN, FP8_PACK_PATTERN, local_only=False)
        self.assertIn('%r20', mapped_at(src, len(text)-1))

    def test_multidef_still_rejected_across_blocks(self):
        text = 'ld.global.v4.u32 {%r20,%r21,%r22,%r23},[%rd10];\n$L_fallback:\n' + BASE
        src = safe_sources(text, FP8_DOWN_PATTERN, FP8_PACK_PATTERN, local_only=False)
        self.assertEqual(src.rejected['%r20'], 'pack_multidef')

if __name__ == '__main__':
    unittest.main()
