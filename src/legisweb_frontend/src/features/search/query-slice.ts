import { type PayloadAction, createSlice } from "@reduxjs/toolkit";

export interface QueryState {
	queryText: string | null;
	documentType: string | null;
}

const initialState: QueryState = {
	queryText: null,
	documentType: null,
};

export const querySlice = createSlice({
	name: "query",
	initialState,
	reducers: {
		submit(state: QueryState, action: PayloadAction<QueryState>) {
			state.queryText = action.payload.queryText;
			state.documentType = action.payload.documentType;
		},
	},
});

export const { submit } = querySlice.actions;
export default querySlice.reducer;