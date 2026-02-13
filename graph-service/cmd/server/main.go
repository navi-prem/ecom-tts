package main

import (
	"log"
	"net"

	pb "github.com/navi-prem/ecom-tts/graph-service/api"
	"github.com/navi-prem/ecom-tts/graph-service/internal/repository"
	"github.com/navi-prem/ecom-tts/graph-service/internal/service"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
	"google.golang.org/grpc"
)

func main() {
	uri := "bolt://localhost:7687"
	username := "neo4j"
	password := "helloworld"

	driver, err := neo4j.NewDriverWithContext(uri, neo4j.BasicAuth(username, password, ""))
	if err != nil {
		log.Fatal(err)
	}
	defer driver.Close(nil)

	repo := repository.NewProductRepository(driver)
	productService := service.NewProductService(repo)

	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatal(err)
	}

	grpcServer := grpc.NewServer()

	pb.RegisterGraphServiceServer(grpcServer, productService)

	log.Println("Graph Service running on :50051")
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatal(err)
	}
}
