
import sys
import os
from binascii import hexlify
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, '..', '..'))

from pcbasic.compat import int2byte
from pcbasic.basic.values import *
import pcbasic.basic.values
from pcbasic.basic.values.numbers import *
from pcbasic.basic.values import numbers


class TestSingle(unittest.TestCase):
    """Test frame for single-precision MBF math."""

    def setUp(self):
        """Create the Values object."""
        self._vm = values.Values(None, False)

        # with open('input/ALLWORD.DAT', 'wb') as f:
        #     for i in range(256):
        #         for j in range(256):
        #             f.write(int2byte(j)+int2byte(i)+'\0'+'\x80')

    def test_single(self):
        """Test MBF single representation."""
        result = []
        for i in range(0, 255):
            a = self._vm.new_single().from_int(i)
            r = self._vm.new_single().from_int(2**23)
            r.iadd(a)
            s = r.clone()
            s.view()[-1:] = int2byte(bytearray(s.view())[-1] + 8)
            t = s.clone()
            result.append(s.iadd(r).isub(t).isub(r).to_value())
        model = [1.0*_i for _i in list(range(0, -129, -1)) + list(range(127, 1, -1))]
        assert result == model

    def test_all_bytes_add(self):
        """Test adding singles, all first-byte combinations."""
        with open('input/ALLWORD.DAT', 'rb') as f:
            with open('model/GWBASABY.DAT', 'rb') as h:
                with open('output/ADDBYTE.DAT', 'wb') as g:
                    while True:
                        buf = bytearray(f.read(4))
                        if len(buf) < 4:
                            break
                        bufl = bytearray('%c\0\0\x80' % buf[0])
                        bufr = bytearray('%c\0\0\x80' % buf[1])
                        l = Single(bufl, self._vm)
                        #bufs = bytes(bufl), bytes(bufr)
                        r = Single(bufr, self._vm)
                        out = bytes(l.iadd(r).to_bytes())
                        g.write(out)
                        inp = h.read(4)
                        assert out == inp
                        #if out != inp:
                        #    print hexlify(out), hexlify(inp)

    def test_all_bytes_sub(self):
        """Test subtracting singles, all first-byte combinations."""
        with open('input/ALLWORD.DAT', 'rb') as f:
            with open ('model/GWBASSBY.DAT', 'rb') as h:
                with open('output/SUBBYTE.DAT', 'wb') as g:
                    while True:
                        buf = bytearray(f.read(4))
                        if len(buf) < 4:
                            break
                        bufl = bytearray('%c\0\0\x80' % buf[0])
                        bufr = bytearray('%c\0\0\x80' % buf[1])
                        l = Single(bufl, self._vm)
                        #bufs = bytes(bufl), bytes(bufr)
                        r = Single(bufr, self._vm)
                        out = bytes(l.isub(r).to_bytes())
                        g.write(out)
                        inp = h.read(4)
                        assert out == inp
                        #if out != inp:
                        #    print hexlify(out), hexlify(inp)

    def test_exponents(self):
        """Test adding with various exponents."""
        for shift in [0,] + range(9, 11):
            r = self._vm.new_single()
            letter = int2byte(ord('0')+shift) if shift<10 else int2byte(ord('A')-10+shift)
            with open('input/ALLWORD.DAT', 'rb') as f:
                with open('model/GWBASAL'+letter+'.DAT', 'rb') as h:
                    with open('output/ALLWORD'+letter+'.DAT', 'wb') as g:
                        while True:
                            l = r
                            l.view()[3:] = int2byte(0x80+shift)
                            buf = bytearray(f.read(4))
                            if len(buf) < 4:
                                break
                            buf[2:] = '\0\x80'
                            r = Single(buf, self._vm)
                            ll = l.clone()
                            #bufs = bytes(l.to_bytes()), bytes(buf)
                            out = bytes(l.iadd(r).to_bytes())
                            g.write(out)
                            inp = h.read(4)
                            #if out != inp:
                            #    print hexlify(out), hexlify(inp)
                            l = ll
                            assert out == inp


    def test_exponents_low(self):
        """Test adding with various exponents."""
        for shift in range(17):
            r = self._vm.new_single()
            letter = int2byte(ord('0')+shift) if shift<10 else int2byte(ord('A')-10+shift)
            with open('input/BYTES.DAT', 'rb') as f:
                with open ('model/GWBASLO'+letter+'.DAT', 'rb') as h:
                    with open('output/LO'+letter+'.DAT', 'wb') as g:
                        while True:
                            l = r
                            l.view()[3:] = int2byte(0x80+shift)
                            buf = bytearray(f.read(4))
                            if len(buf) < 4:
                                break
                            buf[2:] = '\0\x80'
                            r = Single(buf, self._vm)
                            ll = l.clone()
                            #bufs = bytes(l.to_bytes()), bytes(buf)
                            out = bytes(l.iadd(r).to_bytes())
                            g.write(out)
                            inp = h.read(4)
                            #if out != inp:
                            #    print hexlify(out), hexlify(inp)
                            l = ll
                            assert out == inp

    def test_bytes(self):
        """Test additions on random generated byte sequences."""
        fails = {}
        r = self._vm.new_single()
        with open('input/BYTES.DAT', 'rb') as f:
            with open ('model/GWBASADD.DAT', 'rb') as h:
                with open('output/ADD.DAT', 'wb') as g:
                    while True:
                        l = r
                        buf = bytearray(f.read(4))
                        if len(buf) < 4:
                            break
                        r = Single(buf, self._vm)
                        ll = l.clone()
                        #bufs = bytes(l.to_bytes()), bytes(buf)
                        out = bytes(l.iadd(r).to_bytes())
                        g.write(out)
                        inp = h.read(4)
                        if out != inp:
                            fails[hexlify(inp)] = hexlify(out)
                        l = ll
        # two additions are slightly different
        accepted = {
            '920a03ce': '930a03ce',
            '52810dbe': '53810dbe',
        }
        assert fails == accepted

    def test_bigbytes(self):
        """Test additions on random generated byte sequences."""
        fails = {}
        r = self._vm.new_single()
        with open('input/BIGBYTES.DAT', 'rb') as f:
            with open ('model/GWBIGADD.DAT', 'rb') as h:
                with open('output/BIGADD.DAT', 'wb') as g:
                    while True:
                        l = r
                        buf = bytearray(f.read(4))
                        if len(buf) < 4:
                            break
                        r = Single(buf, self._vm)
                        ll = l.clone()
                        #bufs = bytes(l.to_bytes()), bytes(buf)
                        out = bytes(l.iadd(r).to_bytes())
                        g.write(out)
                        inp = h.read(4)
                        if out != inp:
                            fails[hexlify(inp)] = hexlify(out)
                        l = ll
        accepted = {
            '922ed14b': '932ed14b',
            '80c02477': '81c02477',
            'fe4b89df': 'ff4b89df',
            'a9b37594': 'a8b37594',
            'bc3e8549': 'bd3e8549',
            'b2337a91': 'b3337a91',
            '2ef4007a': '2ff4007a'
        }
        assert fails == accepted

    def test_mult(self):
        """Test multiplications on random generated byte sequences."""
        r = self._vm.new_single()
        with open('input/BIGBYTES.DAT', 'rb') as f:
            with open ('model/GWBIGMUL.DAT', 'rb') as h:
                with open('output/BIGMUL.DAT', 'wb') as g:
                    while True:
                        l = r
                        buf = bytearray(f.read(4))
                        if len(buf) < 4:
                            break
                        r = Single(buf, self._vm)
                        ll = l.clone()
                        #bufs = bytes(l.to_bytes()), bytes(buf)
                        try:
                            l.imul(r)
                        except OverflowError:
                            pass
                        out = bytes(l.to_bytes())
                        g.write(out)
                        inp = h.read(4)
                        #if out != inp:
                        #    print hexlify(out), hexlify(inp)
                        l = ll
                        assert out == inp

if __name__ == '__main__':
    unittest.main()
