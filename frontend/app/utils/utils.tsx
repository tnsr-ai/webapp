export const isValidEmail = (email: string) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

export const increaseAndRound = (number: number) => {
  if (number === 0) return 0;
  const increasedNumber = number * 1.1;
  if (increasedNumber < 1) return 1;
  if (increasedNumber < 10) return Math.round(increasedNumber);
  if (increasedNumber < 100) return Math.round(increasedNumber / 10) * 10;
  return Math.round(increasedNumber / 100) * 100;
}