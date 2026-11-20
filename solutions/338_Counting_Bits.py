class Solution(object):
    def countBits(self, n):
        """
        :type n: int
        :rtype: List[int]
        """
        bit_counts = [0] * (n + 1)

        for number in range(1, n + 1):
            previous_number = number >> 1
            last_bit = number & 1
            bit_counts[number] = bit_counts[previous_number] + last_bit
        return bit_counts
