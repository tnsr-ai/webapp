import '@testing-library/jest-dom';
import fetchMock from 'jest-fetch-mock';

global.URL.createObjectURL = jest.fn();
fetchMock.enableMocks(); 