// C++ program to convert decimal 
// number to ternary number 

#include <iostream> 
#include <iomanip>

const uint8_t BASE = 3; ///number of site-holders
const uint8_t BUFF = 6; ///number of sites
///COND[3] = {x, y, z}; means that I require the permutation to have x 0's , y 1's , and z 2's in it for it to be printed
const uint8_t COND [BASE] = {3, 1, 2};

unsigned int ToBase10(const uint8_t, uint8_t *);
void ToBaseN(unsigned int, uint8_t *);
bool Check(const uint8_t, const uint8_t *, const uint8_t, const uint8_t *);
void Print(const uint8_t, uint8_t *);

int main(int charc, char *argv[])
{
	//Get the maximum size base-10 representation
	uint8_t maxSize[BUFF];
	for (uint8_t i = 0; i < BUFF; i++)
		maxSize[i] = BASE - 1;

	//Print all combonations...
	unsigned int count = 0;
	for (unsigned int i = 0; i < ToBase10(BUFF, maxSize); i++)
	{
		uint8_t num[BUFF] = { 0 };
		ToBaseN(i, num);
		//...as long as the sum of the digits is equal to the required condition number
		if (Check(BASE, COND, BUFF, num)) {
			Print(BUFF, num);
			count++;
		}
	}

	//End
	//std::cout << "Total = " << count;
	//std::cin.get();
	return 0;
}

//Converts a base-10 number to a base-BASE, array-represented number of bit length defined by BUFF
void ToBaseN(unsigned int n, uint8_t *arr)
{
	for (uint8_t i = BUFF - 1; i < BUFF; i--)
	{
		arr[i] = (uint8_t)(n % BASE);
		n /= BASE;
	}
	return;
}

//Converts a array-represented number (in base BASE) to base 10
unsigned int ToBase10(const uint8_t size, uint8_t *arr)
{
	unsigned int sum = 0;
	for (int i = 0; i < size; i++)
		sum += (arr[i]) * std::pow(BASE, i);

	return sum;
}

bool Check(const uint8_t reqSize, const uint8_t *req, const uint8_t testSize, const uint8_t *test)
{
	for(uint8_t i = 0; i < reqSize; i++){
		uint8_t count = 0;
		for(uint8_t j = 0; j < testSize; j++){
			if(i == test[j])
				count++;
		}
		if(req[i] != count)
			return false;
	}
	return true;
}

void Print(const uint8_t size, uint8_t *arr)
{
	for (uint8_t i = 0; i < size; i++)
		std::cout << (unsigned)(*(arr + i));
	std::cout << "\n";

	return;
}