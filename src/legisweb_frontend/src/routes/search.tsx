import parse from "html-react-parser";
import { Button, Form, ListGroup, Nav } from "react-bootstrap";
import * as Icon from "react-bootstrap-icons";
import { useDispatch, useSelector } from "react-redux";
import { Link, useLoaderData, useLocation, useSubmit } from "react-router-dom";
import type { RootState } from "../app/store";
import { type QueryState, submit } from "../features/search/query-slice";

interface PersonSearch {
	name: string;
	raw: string;
}

interface HansardSearch {
	id: number;
}

interface InquirySearch {
	id: number;
	number: number;
	is_oral: boolean;
	title: string;
}

interface InquiryTitleSearch {
	content: {
		title: string;
		highlight: string | null;
		number: number;
		is_oral: boolean;
		id: number;
	};
	document_type: string;
	inquirer: PersonSearch;
	respondent: PersonSearch;
}

interface HansardContentSearch {
	hansard: HansardSearch;
	document_type: string;
	content: {
		id: number;
		highlight: string | null;
		value: string;
	};
	person: PersonSearch;
}

interface InquiryContentSearch {
	inquiry: InquirySearch;
	document_type: string;
	content: {
		id: number;
		highlight: string | null;
		value: string;
	};
	person: PersonSearch;
}

function NoResult() {
	return <div>No result is returned</div>;
}

function checkIsDocumentType(
	data:
		| Array<InquiryTitleSearch>
		| Array<HansardContentSearch>
		| Array<InquiryContentSearch>
		| null,
	documentType: string,
): boolean {
	return (
		Array.isArray(data) &&
		data.length > 0 &&
		data[0].document_type === documentType
	);
}

function HansardContentList({
	data,
	documentType,
	anchorPrefix,
}: {
	data: Array<HansardContentSearch> | null;
	documentType: string;
	anchorPrefix: string;
}) {
	if (data == null) {
		return <></>;
	}

	return checkIsDocumentType(data, documentType) ? (
		<ListGroup>
			{data.map((item, idx: number) => (
				<ListGroup.Item key={"li".concat(idx.toString())}>
					<p>{parse(item?.content?.highlight || item?.content?.value)}</p>
					<p>
						<Icon.ListOl />{" "}
						<Link
							to={"/hansard/".concat(
								item?.hansard?.id.toString(),
								"#hansard-",
								anchorPrefix,
								"-",
								item?.content?.id?.toString(),
							)}
						>
							Hansard #{item?.hansard?.id}
						</Link>{" "}
						<Icon.Person />
						<strong>
							{" ".concat(item?.person?.name || "TIDAK TERJUMPA")}
						</strong>
					</p>
				</ListGroup.Item>
			))}
		</ListGroup>
	) : (
		<NoResult />
	);
}
function InquiryContentList({
	data,
	documentType,
}: {
	data: Array<InquiryContentSearch> | null;
	documentType: string;
}) {
	if (data == null) {
		return <></>;
	}

	return checkIsDocumentType(data, documentType) ? (
		<ListGroup>
			{data.map((item, idx: number) => (
				<ListGroup.Item key={"li".concat(idx.toString())}>
					<p>{parse(item?.content?.highlight || item?.content?.value)}</p>
					<p>
						{documentType === "inquiry" ? (
							<Icon.QuestionSquare />
						) : (
							<Icon.FileEarmarkCheck />
						)}
						{documentType === "inquiry"
							? " Jawapan untuk pertanyaan"
							: " Pertanyaan"}
						{item?.inquiry?.is_oral ? " mulut " : " bertulis "}
						bertajuk{" "}
						<Link
							to={"/inquiry/".concat(
								item?.inquiry?.id?.toString() ?? "",
								"#inquiry-",
								documentType === "inquiry" ? "pertanyaan-" : "jawapan-",
								item?.content?.id?.toString() ?? "",
							)}
						>
							{(item?.inquiry?.title ?? "").concat(" ")}
						</Link>
						<Icon.Person />
						<strong>{" ".concat(item?.person?.name ?? "")}</strong>
					</p>
				</ListGroup.Item>
			))}
		</ListGroup>
	) : (
		<NoResult />
	);
}

function InquiryTitleList({
	data,
}: {
	data: Array<InquiryTitleSearch> | null;
}) {
	if (data == null) {
		return <></>;
	}

	return checkIsDocumentType(data, "inquiry-title") ? (
		<ListGroup>
			{data.map((item, idx: number) => (
				<ListGroup.Item key={"li".concat(idx.toString())}>
					<Link to={"/inquiry/".concat(item?.content?.id?.toString())}>
						{parse(
							"#".concat(
								item?.content?.number?.toString(),
								" - ",
								item?.content?.highlight || item?.content?.title,
							),
						)}
					</Link>
					<br />
					<Icon.PersonRaisedHand />{" "}
					<em>
						pertanyaan
						{item?.content?.is_oral ? " mulut " : " bertulis "}
					</em>
					daripada <strong>{item?.inquirer?.name}</strong>
				</ListGroup.Item>
			))}
		</ListGroup>
	) : (
		<NoResult />
	);
}

function TabItem({
	title,
	documentType,
}: { documentType: string; title: string }) {
	const query: QueryState = useSelector((state: RootState) => state.query);
	const dispatch = useDispatch();
	const submitForm = useSubmit();
	return (
		<Nav.Link
			eventKey={documentType}
			onClick={(e) => {
				e.preventDefault();

				const data = {
					queryText: query.queryText,
					documentType: documentType,
				};

				dispatch(submit(data));

				submitForm(data, {
					method: "get",
					action: "/search",
				});
			}}
		>
			{title}
		</Nav.Link>
	);
}

function SearchResult({
	documentType,
	data,
}: {
	documentType: string;
	data:
		| Array<InquiryTitleSearch>
		| Array<HansardContentSearch>
		| Array<InquiryContentSearch>
		| null;
}) {
	return (
		<>
			{documentType === "inquiry-title" && (
				// @ts-expect-error checked already
				<InquiryTitleList data={data} />
			)}
			{documentType === "inquiry" && (
				// @ts-expect-error checked already
				<InquiryContentList data={data} documentType={documentType} />
			)}
			{documentType === "respond" && (
				// @ts-expect-error checked already
				<InquiryContentList data={data} documentType={documentType} />
			)}
			{documentType === "question" && (
				<HansardContentList
					// @ts-expect-error checked already
					data={data}
					documentType={documentType}
					anchorPrefix="pertanyaan"
				/>
			)}
			{documentType === "answer" && (
				<HansardContentList
					// @ts-expect-error checked already
					data={data}
					documentType={documentType}
					anchorPrefix="jawapan"
				/>
			)}
			{documentType === "speech" && (
				<HansardContentList
					// @ts-expect-error checked already
					data={data}
					documentType={documentType}
					anchorPrefix="ucapan"
				/>
			)}{" "}
		</>
	);
}

function SearchForm() {
	const query: QueryState = useSelector((state: RootState) => state.query);
	const search = new URLSearchParams(useLocation().search);
	const dispatch = useDispatch();
	const submitForm = useSubmit();

	const queryText = query.queryText ?? search.get("queryText");
	return (
		<Form
			onSubmit={(e) => {
				e.preventDefault();

				const data = {
					// @ts-expect-error DOM
					queryText: e.target.querySelector("#search-query").value,
					documentType: query.documentType ?? "inquiry-title",
				};

				dispatch(submit(data));

				submitForm(data, {
					method: "get",
					action: "/search",
				});
			}}
		>
			<Form.Group>
				<Form.Label>Query text</Form.Label>
				<Form.Control id="search-query" defaultValue={queryText ?? ""} />
			</Form.Group>
			<Button className="mt-2" variant="primary" type="submit">
				Search
			</Button>
		</Form>
	);
}

export default function Search() {
	const query: QueryState = useSelector((state: RootState) => state.query);
	// @ts-expect-error API
	const data:
		| Array<InquiryTitleSearch>
		| Array<HansardContentSearch>
		| Array<InquiryContentSearch>
		| null = useLoaderData();
	const search = new URLSearchParams(useLocation().search);

	const documentType = query.documentType ?? search.get("documentType");

	return (
		<>
			<h1>Search</h1>
			<SearchForm />

			<h2>
				Search result
				{query.queryText && (
					<>
						{" "}
						for <em>{query.queryText}</em>
					</>
				)}
			</h2>
			<Nav variant="tabs" activeKey={query.documentType ?? "inquiry-title"}>
				<Nav.Item>
					<TabItem documentType="inquiry-title" title="Inquiry Title" />
				</Nav.Item>
				<Nav.Item>
					<TabItem documentType="inquiry" title="Inquiry Content" />
				</Nav.Item>
				<Nav.Item>
					<TabItem documentType="respond" title="Inquiry Respond" />
				</Nav.Item>
				<Nav.Item>
					<TabItem documentType="question" title="Hansard Question" />
				</Nav.Item>
				<Nav.Item>
					<TabItem documentType="answer" title="Hansard Answer" />
				</Nav.Item>
				<Nav.Item>
					<TabItem documentType="speech" title="Hansard Speech" />
				</Nav.Item>
			</Nav>
			<SearchResult documentType={documentType ?? ""} data={data} />
		</>
	);
}
