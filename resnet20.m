Layer CONV1 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 16, C: 3 , R: 3, S: 3, Y: 32, X: 32 }




	}
Layer CONV2_1 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 16, C: 16, R: 3, S: 3, Y: 32, X: 32 }




	}
Layer CONV2_2 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 16, C: 16, R: 3, S: 3, Y: 32, X: 32 }




	}
Layer CONV2_3 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 16, C: 16, R: 3, S: 3, Y: 32, X: 32 }




	}
Layer CONV3_1_1 {
	Type: 
	Stride { X: 2, Y:2}
	Dimensions { K: 32, C: 16, R: 3, S: 3, Y: 32, X: 32 }




	}
Layer CONV3_1_2 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 32, C: 32, R: 3, S: 3, Y: 16, X: 16}



	}
Layer CONV3_1_Residual {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 32, C: 16, R: 1, S: 1, Y: 32, X: 32 }




	}
Layer CONV3_2 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 32, C: 32, R: 3, S: 3, Y: 16, X: 16}




	}
Layer CONV3_3 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 32, C: 32, R: 3, S: 3, Y: 16, X: 16}





	}
Layer CONV4_1_1 {
	Type: 
	Stride { X: 2, Y:2}
	Dimensions { K: 64, C: 32, R: 3, S: 3 , Y: 16, X: 16}




	}
Layer CONV4_1_2 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 64, C: 64, R: 3 , S: 3 , Y: 8 , X: 8}





	}
Layer CONV4_1_Residual {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 64, C: 32, R: 1 , S: 1 , Y: 16, X: 16}





	}
Layer CONV4_2 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 64, C: 64, R: 3 , S: 3 , Y: 8 , X: 8}



	}
Layer CONV4_3 {
	Type: 
	Stride { X: 1, Y:1}
	Dimensions { K: 64, C: 64, R: 3 , S: 3 , Y: 8 , X: 8}



	}

Layer FC10 {
	Type: 
	Stride { X: 1, Y: 1 }		
	Dimensions { K: 10, C: 64, R: 8, S: 8, Y: 8, X: 8 }

	}

}