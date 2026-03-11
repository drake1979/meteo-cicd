FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
RUN apt-get update && apt-get install libnetcdf-dev dos2unix -y

EXPOSE 80
EXPOSE 443

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY FIEK.MET.Backend.sln .

#Project references
COPY FIEK.MET.Backend.Common/FIEK.MET.Backend.Common.csproj ./FIEK.MET.Backend.Common/
COPY FIEK.MET.Backend.Api/FIEK.MET.Backend.Api.csproj ./FIEK.MET.Backend.Api/
COPY FIEK.MET.Backend.Core/FIEK.MET.Backend.Core.csproj ./FIEK.MET.Backend.Core/
COPY FIEK.MET.Backend.Dal/FIEK.MET.Backend.Dal.csproj ./FIEK.MET.Backend.Dal/
COPY Libraries/FIEK.Net.Mail/FIEK.Net.Mail.csproj ./Libraries/FIEK.Net.Mail/

#Project restore
RUN dotnet restore "FIEK.MET.Backend.Api/FIEK.MET.Backend.Api.csproj"
COPY . .

#Project build
WORKDIR /src/FIEK.MET.Backend.Api
RUN dotnet build "FIEK.MET.Backend.Api.csproj" -c Release -o /app/build
RUN dotnet publish "FIEK.MET.Backend.Api.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=build /app/publish .
COPY entrypoint.sh /entrypoint.sh /
RUN dos2unix /entrypoint.sh && chmod +x /entrypoint.sh
RUN sed -i "s/MinProtocol = TLSv1.2/MinProtocol = TLSv1.0/g" /etc/ssl/openssl.cnf && sed -i "s/DEFAULT@SECLEVEL=2/DEFAULT@SECLEVEL=0/g" /etc/ssl/openssl.cnf

ENTRYPOINT [ "/entrypoint.sh" ]
CMD ["dotnet", "FIEK.MET.Backend.Api.dll"]