// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SumLoopExample {
    uint104[] public numbers;
    uint256 public a;

    constructor() {
        // Initialize the array with some values
        numbers = [1, 2];
    }

    // Function to calculate the sum of the array
    function calculateSum() public view returns (uint112) {
        uint112 sum = 0; // Initialize sum to 0
        
        // Loop through the array
        for (uint112 i = 0; i < numbers.length; i++) {
            sum += numbers[i]; // Add each element to the sum
        }
        return sum; // Return the total sum
    }
}
