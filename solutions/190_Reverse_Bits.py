class Solution(object):
    def reverseBits(self, n):
        """
        :type n: int
        :rtype: int
        """
        reverse = 0
        for i in range(32):
            bit = n & 1
            if bit:
                reverse <<= 1
                reverse = reverse | 1
            else:
                reverse <<= 1
            n >>= 1            
        return reverse
