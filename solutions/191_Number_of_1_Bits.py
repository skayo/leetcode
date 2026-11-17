class Solution(object):
    def hammingWeight(self, n):
        """
        :type n: int
        :rtype: int
        """
        countBits = 0
        while n != 0:
            # this will give us the right most bit
            if (n & 1):
                countBits += 1
            # then we shift
            n >>= 1
        return countBits
