export function contentGenerateId(
  contentType: string,
  contentId: number,
  isHansard: boolean = true
) {
  return (isHansard ? "hansard-" : "inquiry-").concat(
    contentType.toLowerCase(),
    "-",
    contentId.toString()
  );
}
