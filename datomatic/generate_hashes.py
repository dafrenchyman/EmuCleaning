import hashlib


class GenerateHashes:
    def generate_sha1(self, file_path):
        h = hashlib.sha1()
        return self._generate(file_path, h)

    def generate_md5(self, file_path):
        h = hashlib.md5()
        return self._generate(file_path, h)

    def _generate(self, file_path, h):
        with open(file_path, "rb") as file:
            while True:
                # Reading is buffered, so we can read smaller chunks.
                chunk = file.read(h.block_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest().upper()
