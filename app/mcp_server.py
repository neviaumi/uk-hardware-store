from enum import Enum
from typing import Union, cast

import mcp.server.fastmcp.prompts as prompts
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

import app.crawlers.diy_dot_com_crawler as diy_dot_com_crawler
import app.crawlers.euro_car_parts_crawler as euro_car_parts_crawler
import app.crawlers.gsf_car_parts_crawler as gsf_car_parts_crawler
import app.crawlers.halfords_crawler.halfords_crawler as halfords_crawler
import app.crawlers.homebase_crawler.homebase_crawler as homebase_crawler
import app.crawlers.robert_dyas_crawler as robert_dyas_crawler
import app.crawlers.screwfix_crawler as screwfix_crawler
import app.crawlers.toolstation_crawler as toolstation_crawler
import app.crawlers.wickes_crawler as wickes_crawler
from app.logger import get_logger_for_mcp_server

mcp_logger = get_logger_for_mcp_server("mcp-server")


class Provider(str, Enum):
    DIY_DOT_COM = diy_dot_com_crawler.SOURCE_IDENTIFIER
    EURO_CAR_PARTS = euro_car_parts_crawler.SOURCE_IDENTIFIER
    GSF_CAR_PARTS = gsf_car_parts_crawler.SOURCE_IDENTIFIER
    HALFORDS = halfords_crawler.SOURCE_IDENTIFIER
    HOMEBASE = homebase_crawler.SOURCE_IDENTIFIER
    ROBERT_DYAS = robert_dyas_crawler.SOURCE_IDENTIFIER
    SCREWFIX = screwfix_crawler.SOURCE_IDENTIFIER
    TOOLSTATION = toolstation_crawler.SOURCE_IDENTIFIER
    WICKES = wickes_crawler.SOURCE_IDENTIFIER


class CarPartProvider(str, Enum):
    EURO_CAR_PARTS = euro_car_parts_crawler.SOURCE_IDENTIFIER
    GSF_CAR_PARTS = gsf_car_parts_crawler.SOURCE_IDENTIFIER
    HALFORDS = halfords_crawler.SOURCE_IDENTIFIER


mcp = FastMCP(
    "Hardware Store",
    streamable_http_path="/",
    host="0.0.0.0",
    json_response=True,
    stateless_http=True,
)


@mcp.prompt("Hardware store staff", "Helpful assistant for a UK hardware store project")
def hardware_store_staff() -> list[prompts.base.Message]:
    return [
        prompts.base.UserMessage(
            content="""You are a knowledgeable hardware store assistant with expertise in DIY tools and equipment. Your role is to:

1. UNDERSTAND REQUIREMENTS:
- Listen carefully to customer needs and use cases.
- Ask clarifying questions about their project (e.g., "What material are you drilling into?", "Is this for indoor or outdoor use?") to suggest the most appropriate tools.
- Consider the user's skill level and safety requirements.

2. PRODUCT RECOMMENDATIONS:
- Search across B&Q (diy.com), Euro Car Parts, GSF Car Parts, Halfords, Homebase, Screwfix, Toolstation, and Wickes.
- Provide 2-3 best options that match the customer's needs.
- Include price comparisons across different stores when available.
- Always include direct product URLs.

3. PRODUCT INFORMATION:
- Present key features and specifications clearly.
- Explain WHY each recommendation suits their specific project.
- Include relevant safety information or mandatory accessories (e.g., "You'll need a SDS bit for this drill").
- Mention ongoing promotions if available.

4. INTERACTION STYLE:
- Be friendly, professional, and practical.
- Use clear, jargon-free language.
- Offer follow-up assistance for maintenance or usage tips.

Format your product recommendations as follows:
• Product Name
• Price
• Store Link
• Key Features
• Why it's recommended

Wait for the user to describe their project before offering specific product links."""
        ),
        prompts.base.AssistantMessage(
            content="""Welcome to the Hardware Store! I'm here to help you find the perfect tools and supplies for your DIY projects. To give you the best advice, could you please tell me a bit more about what you're planning to work on today?"""
        ),
    ]


class ProviderInfo(BaseModel):
    name: str = Field(description="The provider name/identifier.")
    description: str = Field(
        description="A description of the products this provider sells."
    )


@mcp.tool(
    "get_providers",
    title="Get Providers",
    description="Get a list of available hardware store providers and descriptions of the products they sell. Use this to determine which provider to query based on what the user is looking for.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def get_providers() -> list[ProviderInfo]:
    return [
        ProviderInfo(
            name=diy_dot_com_crawler.SOURCE_IDENTIFIER,
            description=diy_dot_com_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=euro_car_parts_crawler.SOURCE_IDENTIFIER,
            description=euro_car_parts_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=gsf_car_parts_crawler.SOURCE_IDENTIFIER,
            description=gsf_car_parts_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=halfords_crawler.SOURCE_IDENTIFIER,
            description=halfords_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=homebase_crawler.SOURCE_IDENTIFIER,
            description=homebase_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=robert_dyas_crawler.SOURCE_IDENTIFIER,
            description=robert_dyas_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=screwfix_crawler.SOURCE_IDENTIFIER,
            description=screwfix_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=toolstation_crawler.SOURCE_IDENTIFIER,
            description=toolstation_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=wickes_crawler.SOURCE_IDENTIFIER,
            description=wickes_crawler.SOURCE_DESCRIPTION,
        ),
    ]


@mcp.tool(
    "get_car_part_providers",
    title="Get Car Part Providers",
    description="Get a list of available car part hardware store providers and descriptions of the products they sell. Use this to determine which provider to query for car parts search.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def get_car_part_providers() -> list[ProviderInfo]:
    return [
        ProviderInfo(
            name=euro_car_parts_crawler.SOURCE_IDENTIFIER,
            description=euro_car_parts_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=gsf_car_parts_crawler.SOURCE_IDENTIFIER,
            description=gsf_car_parts_crawler.SOURCE_DESCRIPTION,
        ),
        ProviderInfo(
            name=halfords_crawler.SOURCE_IDENTIFIER,
            description=halfords_crawler.SOURCE_DESCRIPTION,
        ),
    ]


class ProductDetailRequest(BaseModel):
    product_url: str = Field(
        description="The absolute product URL (e.g., `https://www.diy.com/products/hammer-12345`)."
    )


ProductDetailResponse = Union[
    diy_dot_com_crawler.ProductDetailResponse,
    euro_car_parts_crawler.ProductDetailResponse,
    gsf_car_parts_crawler.ProductDetailResponse,
    halfords_crawler.ProductDetailResponse,
    homebase_crawler.ProductDetailResponse,
    robert_dyas_crawler.ProductDetailResponse,
    screwfix_crawler.ProductDetailResponse,
    toolstation_crawler.ProductDetailResponse,
    wickes_crawler.ProductDetailResponse,
]


@mcp.tool(
    "get_product_detail",
    title="Get Product Detail",
    description="Fetch comprehensive product details (specifications, description, price) using a store URL from a specific UK hardware retailer.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def get_product_detail(
    provider: Provider = Field(
        description="The UK hardware retailer to fetch details from. See get_providers for available options."
    ),
    request: ProductDetailRequest = Field(
        description="The request containing the product URL."
    ),
) -> ProductDetailResponse:
    mcp_logger.info(
        f"Fetching product details from {provider}, url: {request.product_url}",
    )
    match provider:
        case Provider.DIY_DOT_COM:
            result = await diy_dot_com_crawler.product_detail(request.product_url)
        case Provider.EURO_CAR_PARTS:
            result = await euro_car_parts_crawler.product_detail(request.product_url)
        case Provider.GSF_CAR_PARTS:
            result = await gsf_car_parts_crawler.product_detail(request.product_url)
        case Provider.HALFORDS:
            result = await halfords_crawler.product_detail(request.product_url)
        case Provider.HOMEBASE:
            result = await homebase_crawler.product_detail(request.product_url)
        case Provider.ROBERT_DYAS:
            result = await robert_dyas_crawler.product_detail(request.product_url)
        case Provider.SCREWFIX:
            result = await screwfix_crawler.product_detail(request.product_url)
        case Provider.TOOLSTATION:
            result = await toolstation_crawler.product_detail(request.product_url)
        case Provider.WICKES:
            result = await wickes_crawler.product_detail(request.product_url)
        case _:
            raise ToolError(f"Provider {provider} is not supported.")

    return result


class ProductsSearchRequest(BaseModel):
    keyword: str = Field(
        description="The search term (e.g., 'M6 Hex Bolt', 'Combi Drill') to query the catalog."
    )


ProductSearchResponse = list[
    Union[
        diy_dot_com_crawler.ProductSearchResponse,
        euro_car_parts_crawler.ProductSearchResponse,
        gsf_car_parts_crawler.ProductSearchResponse,
        halfords_crawler.ProductSearchResponse,
        homebase_crawler.ProductSearchResponse,
        robert_dyas_crawler.ProductSearchResponse,
        screwfix_crawler.ProductSearchResponse,
        toolstation_crawler.ProductSearchResponse,
        wickes_crawler.ProductSearchResponse,
    ]
]


@mcp.tool(
    "search_products",
    title="Search Products",
    description="Search for products on a specific UK hardware retailer's catalog. If you aren't sure which provider to use, check the get_providers tool.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def search_products(
    provider: Provider = Field(
        description="The UK hardware retailer to search on. See get_providers for options."
    ),
    request: ProductsSearchRequest = Field(
        description="The search request containing the keyword."
    ),
) -> ProductSearchResponse:
    mcp_logger.info(f"Searching for '{request.keyword}' on {provider}")
    match provider:
        case Provider.DIY_DOT_COM:
            result = await diy_dot_com_crawler.product_search(request.keyword)
        case Provider.EURO_CAR_PARTS:
            result = await euro_car_parts_crawler.product_search(request.keyword)
        case Provider.GSF_CAR_PARTS:
            result = await gsf_car_parts_crawler.product_search(request.keyword)
        case Provider.HALFORDS:
            result = await halfords_crawler.product_search(request.keyword)
        case Provider.HOMEBASE:
            result = await homebase_crawler.product_search(request.keyword)
        case Provider.ROBERT_DYAS:
            result = await robert_dyas_crawler.product_search(request.keyword)
        case Provider.SCREWFIX:
            result = await screwfix_crawler.product_search(request.keyword)
        case Provider.TOOLSTATION:
            result = await toolstation_crawler.product_search(request.keyword)
        case Provider.WICKES:
            result = await wickes_crawler.product_search(request.keyword)
        case _:
            raise ToolError(f"Provider {provider} is not supported.")

    return cast(ProductSearchResponse, result)


class CarPartsSearchRequest(BaseModel):
    car_plate: str = Field(
        description="The vehicle registration plate (e.g., 'NX60OLA')."
    )
    keyword: str = Field(
        description="The car part or accessory search term (e.g., 'Engine Oil', 'Brake Pads')."
    )


CarPartsProductSearchResponse = list[
    Union[
        halfords_crawler.ProductSearchResponse,
        euro_car_parts_crawler.ProductSearchResponse,
        gsf_car_parts_crawler.ProductSearchResponse,
    ]
]


@mcp.tool(
    "search_car_parts",
    title="Search Car Parts by Registration Plate",
    description="Search for vehicle-compatible car parts on supported retailers (GSF Car Parts, Halfords, or Euro Car Parts) using a vehicle registration plate and keyword.",
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def search_car_parts(
    request: CarPartsSearchRequest = Field(
        description="The request containing the vehicle registration plate and keyword."
    ),
    provider: CarPartProvider = Field(
        description="The UK retailer to search car parts on (GSF Car Parts, Halfords, or Euro Car Parts). See get_car_part_providers for options."
    ),
) -> CarPartsProductSearchResponse:
    mcp_logger.info(
        f"Searching car parts on {provider} for plate '{request.car_plate}' and keyword '{request.keyword}'"
    )
    match provider:
        case CarPartProvider.HALFORDS:
            res = await halfords_crawler.car_parts_product_search(
                request.car_plate, request.keyword
            )
            return cast(CarPartsProductSearchResponse, res)
        case CarPartProvider.EURO_CAR_PARTS:
            res = await euro_car_parts_crawler.car_parts_product_search(
                request.car_plate, request.keyword
            )
            return cast(CarPartsProductSearchResponse, res)
        case CarPartProvider.GSF_CAR_PARTS:
            res = await gsf_car_parts_crawler.car_parts_product_search(
                request.car_plate, request.keyword
            )
            return cast(CarPartsProductSearchResponse, res)
        case _:
            raise ToolError(f"Provider {provider} does not support car parts search.")
