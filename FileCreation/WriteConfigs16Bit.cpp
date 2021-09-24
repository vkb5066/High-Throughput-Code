#include <iostream>
#include <fstream>
#include <bitset>

uint8_t CountBits(uint16_t);

int main(int argc, char *argv[])
{	
	std::ofstream outfile("seeds");

	uint16_t count = 1;
	while(count > 0){
		if(CountBits(count) == 8) ///charge neutrality
			outfile << std::bitset<16>(count) << "\n";
		count++;
	}

	outfile.close();
	return 0;
}

uint8_t CountBits(uint16_t n)
{
	if (n == 0)
		return 0;
	else
		return (n&1) + CountBits(n >> 1);
}