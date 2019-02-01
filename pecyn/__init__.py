# Copyright 2018 by Kurt Griffiths
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from base64 import b64decode, b64encode
import gzip
import struct

import msgpack

# -----------------------------------------------------------------------------
# NOTE(kgriffs): Version header is 1 bytes, so version may not exceed 255.
# -----------------------------------------------------------------------------
_PACK_VERSION = 0x00

# -----------------------------------------------------------------------------
# NOTE(kgriffs): Once added, these flags can never be changed without
#   increasing the version number header and providing for backwards-
#   compatibility (switching on the version header).
#
#   The flag header for (_PACK_VERSION == 0) is 8 bits in size.
# -----------------------------------------------------------------------------
_FLAG_MSGPACK = 0x01 << 0
_FLAG_GZIP = 0x01 << 4

# -----------------------------------------------------------------------------
_HEADER_BLOCK_SIZE = 2
_GZIP_COMPRESSION_LEVEL = 3


def pack(doc, compress=None):
    """Serialize a document to a Base64-encoded string.

    Arguments:
        doc: The string, dict, array, or other JSON-compatible
            object to serialize.

    Keyword Arguments:
        compress: Set to True in order to compress the
            result (defaults to False if not set).

    Returns:
        str: Serialized document.
    """

    return b64encode(packb(doc, compress=compress)).decode()


def unpack(record):
    """Deserialize a document previously serialized with pack().

    Arguments:
        record (str): Byte string to deserialize.

    Returns:
        doc: Deserialized JSON-compatible object.
    """

    return unpackb(b64decode(record))


def packb(doc, compress=None):
    """Serialize a document to a byte string.

    Arguments:
        doc: The string, dict, array, or other JSON-compatible
            object to serialize.

    Keyword Arguments:
        compress: Set to True in order to compress the
            result (defaults to False if not set).

    Returns:
        bytes: Serialized document.
    """

    flags = _FLAG_MSGPACK
    blob = msgpack.packb(doc, use_bin_type=True)
    if compress:
        blob = gzip.compress(blob, _GZIP_COMPRESSION_LEVEL)
        flags |= _FLAG_GZIP

    header_block = struct.pack('BB', _PACK_VERSION, flags)
    record = header_block + blob

    return record


def unpackb(record):
    """Deserialize a document previously serialized with packb().

    Arguments:
        record (bytes): Byte string to deserialize.

    Returns:
        doc: Deserialized JSON-compatible object.
    """

    header_block = record[:_HEADER_BLOCK_SIZE]

    if header_block[0] != _PACK_VERSION:
        raise ValueError('Unsupported pack version: {}'.format(header_block[0]))

    flags = header_block[1]

    if (flags & _FLAG_GZIP):
        blob = gzip.decompress(record[_HEADER_BLOCK_SIZE:])
    else:
        blob = record[_HEADER_BLOCK_SIZE:]

    if not (flags & _FLAG_MSGPACK):
        raise ValueError('Unsupported document format: {}'.format(flags))

    return msgpack.unpackb(blob, raw=False)
