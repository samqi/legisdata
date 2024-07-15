import { createBrowserRouter } from "react-router-dom";
import Hansard from "./routes/hansard";
import HansardList from "./routes/hansard-list.tsx";
import InquiryList from "./routes/inquiry-list.tsx";
import Inquiry from "./routes/inquiry.tsx";
import Root from "./routes/root";
import Search from "./routes/search.tsx";

const router = createBrowserRouter([
	{
		path: "/",
		element: <Root />,
		children: [
			{
				path: "hansard",
				element: <HansardList />,
				// @ts-expect-error API
				// eslint-disable-next-line @typescript-eslint/no-unused-vars
				loader: async ({ request, param }) => fetch("/api/hansard.json"),
			},
			{
				path: "hansard/:hansardId",
				element: <Hansard />,
				// @ts-expect-error API
				// eslint-disable-next-line @typescript-eslint/no-unused-vars
				loader: async ({ request, params }) =>
					fetch(
						"/api/hansard/".concat(
							params.hansardId || "",
							".json?",
							new URLSearchParams({ expand: "~all" }).toString(),
						),
					),
			},
			{
				path: "inquiry",
				element: <InquiryList />,
				// @ts-expect-error API
				// eslint-disable-next-line @typescript-eslint/no-unused-vars
				loader: async ({ request, param }) => fetch("/api/inquiry.json"),
			},
			{
				path: "inquiry/:inquiryId",
				element: <Inquiry />,
				// @ts-expect-error API
				// eslint-disable-next-line @typescript-eslint/no-unused-vars
				loader: async ({ request, params }) =>
					fetch(
						"/api/inquiry/".concat(
							params.inquiryId || "",
							".json?",
							new URLSearchParams({ expand: "~all" }).toString(),
						),
					),
			},
			{
				path: "search",
				element: <Search />,
				loader: async ({ request }) => {
					const url = new URL(request.url);
					const data = new URLSearchParams(url.search);

					if (data.get("queryText") == null) {
						return undefined;
					}

					return fetch(
						"/api/search?".concat(
							new URLSearchParams({
								query: data.get("queryText") ?? "",
								document_type: data.get("documentType") ?? "",
							}).toString(),
						),
						{
							method: "GET",
						},
					);
				},
			},
		],
	},
]);

export default router;
