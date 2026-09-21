from typing import Dict, Any, Tuple
from ..codecs.ncc_vcl import NCCVCLCodec
from ..codecs.structured_text import StructuredTextCodec

class SemanticVerifier:
    """
    Semantic round-trip verifier and fail-open manager.
    Checks critical assertions and triggers fallback if lossy compression corrupts semantics.
    """
    @classmethod
    def verify_and_encode(
        cls,
        assertions: list,
        invariants: list,
        codec_name: str = "ncc_vcl"
    ) -> Tuple[str, str, bool]:
        if codec_name == "ncc_vcl":
            encoded_text, checksum = NCCVCLCodec.encode_packet(assertions, invariants)
            # Round-trip sanity test
            lines = encoded_text.splitlines()
            valid_count = 0
            for line in lines:
                if line.startswith("["):
                    decoded = NCCVCLCodec.decode_line(line)
                    if decoded.get("valid"):
                        valid_count += 1

            # If round trip decoding fails, fall back open to Structured Text
            if len(assertions) > 0 and valid_count == 0:
                fb_text, fb_checksum = StructuredTextCodec.encode_packet(assertions, invariants)
                return fb_text, fb_checksum, False

            return encoded_text, checksum, True
        else:
            encoded_text, checksum = StructuredTextCodec.encode_packet(assertions, invariants)
            return encoded_text, checksum, True
